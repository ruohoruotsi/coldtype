import datetime

from subprocess import run
from defcon import Font as DFont
from coldtype.geometry.rect import Rect
from coldtype.helpers import glyph_to_uni
from coldtype.timing.timeline import Timeline
from coldtype.renderable import renderable, animation
from coldtype.text.composer import Style, Font, StSt
from coldtype.runon.path import P
from coldtype.color import hsl
from pathlib import Path

from typing import Tuple


class glyphfn():
    def __init__(self, width=1000, lsb=None, rsb=None, glyph_name=None):
        """lsb = left-side-bearing / rsb = right-side-bearing"""
        self.width = width
        self.lsb = lsb
        self.rsb = rsb
        self.frame = None
        self.bbox = None
        self._glyph_name_override = glyph_name
    
    def add_font(self, font):
        width = self.width
        if width == "auto":
            width = self.func(None).ambit(tx=0,ty=0).w
        
        if self.lsb is None:
            if font.default_lsb is not None:
                self.lsb = font.default_lsb
            else:
                self.lsb = 10
        
        if self.rsb is None:
            if font.default_rsb is not None:
                self.rsb = font.default_rsb
            else:
                self.rsb = 10

        self.frame = Rect(width, font.ufo.info.capHeight)
        self.bbox = Rect(self.lsb + width + self.rsb, font.ufo.info.capHeight)
        return self
    
    def __call__(self, func):
        self.func = func
        self.glyph_name = func.__name__
        if self._glyph_name_override is not None:
            self.glyph_name = self._glyph_name_override
        self.unicode = glyph_to_uni(self.glyph_name)
        return self


class generativefont(animation):
    def __init__(self,
        lookup,
        ufo_path:Path,
        font_name="Test",
        style_name="Regular",
        cap_height=750,
        ascender=750,
        descender=-250,
        units_per_em=1000,
        preview_size=(1000, None),
        default_lsb=None,
        default_rsb=None,
        filter=None):

        pw, ph = preview_size
        self.preview_frame = Rect(pw, ph if ph else (-descender*2) + cap_height)

        if not ufo_path.exists():
            ufo = DFont()
            ufo.save(ufo_path)
        else:
            ufo = DFont(str(ufo_path))
        
        ufo.info.familyName = font_name
        ufo.info.styleName = style_name
        ufo.info.capHeight = cap_height
        ufo.info.ascender = ascender
        ufo.info.descender = descender
        ufo.info.unitsPerEm = units_per_em
        
        self.ufo = ufo
        
        self.default_lsb = default_lsb
        self.default_rsb = default_rsb
        
        self.filter = filter

        super().__init__(
            self.preview_frame, timeline=self.timeline(lookup),
            postfn=generativefont.ShowGrid)
    
    def _find_glyph_fns(self, lookup):
        """
        `lookup` should probably be `globals()`
        """
        self.glyph_fns = []
        itms = lookup.items()
        for k, v in itms:
            if isinstance(v, glyphfn):
                self.glyph_fns.append(v)
    
    def timeline(self, lookup):
        self._find_glyph_fns(lookup)
        return Timeline(len(self.glyph_fns))
    
    def frame_to_fn(self, fi) -> Tuple[str, dict]:
        return [
            f"def {self.glyph_fns[fi].glyph_name}(",
            dict(decorator="@glyphfn")]
    
    def ShowGrid(render, result):
        if False: # flip to true if you don't want to see the grid
            return result

        gfn = result[0].data("gfn")
        if not gfn:
            print("! No glyph found")
            return result
        
        try:
            guides = result[0].all_guides()
        except:
            guides = P()

        glyph_copy = gfn.func(gfn.frame).scale(0.5).align(render.rect.inset(20), "E")
        
        bbox = gfn.bbox.offset(0, 250)
        return P([
            P(result).translate(0, 250),
            #P().gridlines(render.rect).s(hsl(0.6, a=0.3)).sw(1).f(None),
            (P()
                .line(bbox.es.extr(-100))
                .line(bbox.en.extr(-100))
                .line(bbox.ee.extr(-100))
                .f(None).s(hsl(0.9, 1, a=0.5)).sw(4)),
            glyph_copy.pen().f(0),
            guides.translate(gfn.lsb, 250),
            (P().text(gfn.glyph_name, Style("Times", 48, load_font=0),
                render.rect.inset(50)))])
    
    def glyphViewer(self, f):
        glyph_fn = self.glyph_fns[f.i]
        glyph_fn.add_font(self)

        print(f"> drawing :{glyph_fn.glyph_name}:")
        glyph_pen = (glyph_fn
            .func(glyph_fn.frame)
            .fssw(-1, 0, 2))
        
        tx = 0
        if glyph_fn.width == "auto":
            tx = glyph_pen.ambit(tx=0, ty=0).x
        
        if self.filter:
            glyph_pen = self.filter(glyph_pen)
        
        glyph_pen.translate(-tx, 0)

        # shift over by the left-side-bearing
        glyph_pen.translate(glyph_fn.lsb, 0)
        glyph_pen_no_guides = (glyph_pen
            .copy()
            .remove(lambda el: el.tag() == "guide"))

        glyph = glyph_pen_no_guides.toGlyph(
            name=glyph_fn.glyph_name,
            width=glyph_fn.frame.w + glyph_fn.lsb + glyph_fn.rsb,
            allow_blank = True)
        glyph.unicode = glyph_to_uni(glyph_fn.glyph_name)
        self.ufo.insertGlyph(glyph)
        self.ufo.save()
        return P([
            glyph_pen.data(gfn=glyph_fn, function_literals=True)
        ])
    
    def spacecenter(self, r, text, fontSize=150, idx=None):
        """
        This function loads the ufo that’s been created by the code above and displays it "as a font" (i.e. it compiles the ufo to a font and then uses the actual font to do standard font-display logic)
        """
        if text == "auto":
            text = "".join([chr(x.unicode) for x in self.glyph_fns])
        
        ufo = Font(self.ufo.path)
        txt = (StSt(text, ufo, fontSize)
            .align(r)
            .f(0))
        
        if idx is not None:
            txt.centerPoint(r, (idx, "C"))

        return txt

    def fontmake(self):
        ufo = DFont(self.ufo.path)
        date = datetime.datetime.now().strftime("%y%m%d%H%M")
        font_name = "_".join([
            ufo.info.familyName.replace(" ", ""),
            ufo.info.styleName.replace(" ", ""),
            date
        ])
        fontmade_path = Path(self.ufo.path).parent / f"fontmakes/{font_name}.otf"
        fontmade_path.parent.mkdir(exist_ok=True)
        run([
            "fontmake",
            "-u", str(self.ufo.path),
            "-o", "otf",
            "--output-path=" + str(fontmade_path)])