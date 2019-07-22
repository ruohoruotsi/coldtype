import os
import sys
import time

dirname = os.path.realpath(os.path.dirname(__file__))
if __name__ == "__main__":
    sys.path.append(f"{dirname}/../..")

from fontTools.pens.basePen import BasePen
from fontTools.pens.transformPen import TransformPen
from fontTools.misc.transform import Transform
from coldtype.geometry import Rect, Edge, Point
from coldtype.pens.svgpen import SVGPen
from coldtype.pens.datpen import DATPen
from coldtype.viewer import viewer

import math
try:
    from pyaxidraw import axidraw
except:
    pass

MOVE_DELAY = 0

class AxiDrawPen(BasePen):
    def __init__(self, dat, page):
        super().__init__(None)
        self.dat = dat
        self.page = page
        self.ad = None
        #dat.replay(self)
        self.last_moveTo = None
    
    def _moveTo(self, p):
        self.last_moveTo = p
        time.sleep(MOVE_DELAY)
        self.ad.moveto(*p)
        time.sleep(MOVE_DELAY)

    def _lineTo(self, p):
        self.ad.lineto(*p)

    def _curveToOne(self, p1, p2, p3):
        print("CANNOT CURVE")

    def _qCurveToOne(self, p1, p2):
        print("CANNOT CURVE")

    def _closePath(self):
        # can this work?
        if self.last_moveTo:
            self.ad.lineto(*self.last_moveTo)

    def draw(self, scale=0.01, dry=True):
        if dry:
            with viewer() as v:
                dp = DATPen().record(self.dat).addAttrs(fill=None, stroke=0)
                v.send(SVGPen.Composite([dp], self.page), self.page)
        else:
            self.dat.scale(scale)
            self.page = self.page.scale(scale)
            b = self.dat.bounds()
            if b.x >= 0 and b.y >= 0 and b.w <= 11 and b.h <= 8.5:
                print("Drawing!")
            else:
                print("Too big!", b)
                return False
            ad = axidraw.AxiDraw()
            ad.interactive()
            ad.options.speed_pendown = 70
            ad.options.speed_penup = 110

            ad.connect()
            ad.penup()
            self.ad = ad
            tp = TransformPen(self, (1, 0, 0, -1, 0, self.page.h))

            self.dat.replay(tp)
            time.sleep(MOVE_DELAY)
            ad.penup()
            ad.moveto(0,0)
            ad.disconnect()


if __name__ == "__main__":
    sys.path.insert(0, os.path.realpath("."))
    from coldtype.viewer import viewer
    from coldtype.pens.datpen import DATPenSet
    from coldtype import Slug, Style
    from coldtype.ufo import UFOStringSetter
    from random import random, randint
    from string import ascii_lowercase, ascii_uppercase
 
    def text_test():
        def frame(c, r):
            p = Slug(c, Style("≈/HalunkeV0.2-Regular.otf", 300)).pen()
            p.align(r).rotate(-45) #.flatten()
            return p
        
        time.sleep(1)
        r = Rect(0, 0, 500, 500)
        for c in ascii_uppercase:
            time.sleep(2)
            ap = AxiDrawPen(frame(c, r), r)
            ap.draw(dry=1)
    
    text_test()