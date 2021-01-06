from coldtype.test import *
from coldtype.midi.controllers import LaunchControlXL

swear = Font.Cacheable("~/Type/fonts/fonts/SwearRomanVariable.ttf")


@renderable(bg=1, rstate=1)
def draw1(r, rs):
    #nxl = LaunchControlXL(rs.midi)
    current = DATPen()
    strokes = DATPens()
    #wdth = nxl(20)*150
    #angle = nxl(10)*180

    def draw_item(item, midi=None):
        if item:
            p = item.position
            _nxl = LaunchControlXL(midi or item.midi)
            angle = _nxl(10)*-90-90
            wdth = _nxl(20)*150+5
            nib = _nxl(30)*20+1
            to = DATPen()
            to.line([p.project(angle-180, wdth), p.project(angle, wdth)]).s(0).sw(nib)
            return to

    for g in rs.input_history.strokes(lambda g: g.action == "down" and g.keylayer == Keylayer.Editing and len(g) > 1):
        for item in g:
            strokes += draw_item(item)
    
    editing = rs.keylayer == Keylayer.Editing
    
    if editing:
        current.record(draw_item(rs.input_history.last(), rs.midi))

    return (DATPenSet([
        DATPen().rect(r.inset(5)).f(None).s(0).sw(5) if editing else DATPen().rect(r).f(1),
        #StyledString("a", Style(swear, 1000, wght=0.5)).pen().align(r).f(hsl(0.5)),
        current.s(0.5).sw(10),
        (DATPens([strokes])
            #.s(hsl(0.9))
            #.sw(10)
            .s(hsl(0.7) if editing else 0)
            #.sw(15)
            #.f(1)
            .color_phototype(r, blur=5, cut=190)
            .img_opacity(0.5 if editing else 1))]))