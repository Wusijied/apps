#!/usr/bin/env python3
"""gen_e36.py - writes the E36 cluster theme's layout (Cluster Themes "e36").

    python3 tools/gen_e36.py apps/cluster_themes/hud/layouts/e36.json

The BMW E36 328i cluster of the 90s, traced off face-on photos kept next to the repo in ../design/photos/e36/:
eu-kmh-day-face.png (the metric face) and us-mph-day-face.png (the mph face). Every measurement below is in that
photo's pixels, levelled (pairs that sit at one height on the car, like the two big hubs, take their average);
place() scales a face to the cluster at true proportions, the lamp strips in the bottom row (y 660..720), where BMW's
gear letter shows through the right strip (x 1380..1460).

Angles are degrees clockwise from 12 o'clock, round the needle's pivot. A dial's "map" is [value, angle] pairs
read off its printed scale (shared/e36.js frac()); "rest" is where the needle lies with no data (on its pin).
The figures and labels are text widgets on top (fonts e_num, e_sm, e_lcd: tools/bake_fonts.py).

Edit this file, not the JSON.
"""
import copy
import json
import math
import os
import sys

W, H, ROW = 1920, 720, 660           # the cluster; BMW's strip row is y 660..720
GEAR = (1380, 1460)                  # BMW's gear letter shows through here, in the strip row


def lerp_ang(table, v):
    """The angle at value v on a [(value, angle)] scale (rising values)."""
    for (a, x), (b, y) in zip(table, table[1:]):
        if a <= v <= b:
            return x + (y - x) * (v - a) / (b - a)
    raise ValueError(v)


FONTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'apps', 'cluster_themes', 'hud', 'fonts')
_fonts = {}


def font(name):
    """A baked font's metrics (tools/bake_fonts.py): cell height and each glyph's advance."""
    if name not in _fonts:
        with open(os.path.join(FONTS, name + '.json')) as f:
            _fonts[name] = json.load(f)
    return _fonts[name]


def text_widget(wid, text, fname, cx, cy, toggle, color='mark'):
    """A text widget centred on (cx, cy), just wide enough for its text."""
    f = font(fname)
    w = sum(f['glyphs'][c]['advance'] for c in text) + 4
    h = f['cellHeight']
    return {'id': wid, 'type': 'text', 'class': 'content', 'z': 5, 'x': round(cx - w / 2), 'y': round(cy - h / 2),
            'w': w, 'h': h, 'text': text, 'font': fname, 'color': color, 'align': 'center', 'toggle': toggle}


# --- the metric (EU) face, eu-kmh-day-face.png (2000 x 1500) ----------------------------------------------------
TACH_ANG = [(0, -116.6), (1000, -92.0)] + [(1000 * k, -92.0 + 34.77 * (k - 1)) for k in range(2, 8)]
EU_ECON_TICKS = [   # outer end, inner end (photo px), width: 0 .. 30 L/100km every 2, the 0, 10, 20, 30 marks wide
    ((1102, 907), (1120, 895), 6), ((1110, 925), (1128, 916), 2.5), ((1130, 947), (1153, 923), 2.5),
    ((1152, 958), (1170, 932), 2.5), ((1172, 960), (1187, 940), 2.5), ((1197, 960), (1205, 943), 6),
    ((1217, 960), (1220, 950), 2.5), ((1237, 960), (1238, 952), 2.5), ((1257, 960), (1258, 952), 2.5),
    ((1277, 962), (1275, 952), 2.5), ((1292, 963), (1285, 948), 6), ((1312, 960), (1318, 945), 2.5),
    ((1328, 958), (1342, 938), 2.5), ((1348, 957), (1363, 932), 2.5), ((1370, 958), (1390, 940), 2.5),
    ((1413, 925), (1382, 905), 6),
]
EU = {
    'photo': 'eu-kmh-day-face.png',
    'mph': False,
    'face': {'box': [100, 470, 1900, 1075], 'radius': 190, 'arch': [1000, 2290, 1820], 'bezel': 40},
    'strips': [[420, 993, 330, 65], [765, 993, 470, 65], [1250, 993, 330, 65]], 'stripR': 12,
    'windows': [[617, 862, 268, 95, 6], [915, 498, 195, 62, 6], [957, 930, 92, 55, 6]],   # LCD, top lamp, ASC
    'arrows': [[457, 669, 55, -1], [1562, 669, 55, 1]],
    'knob': [462, 965, 22], 'sensor': [1488, 950, 16],
    'dials': [
        {'signal': 'fuel', 'c': [347, 845], 'r': 132, 'pivot': [338, 902], 'hub': 24, 'tail': 18, 'needle': [130, 7],
         'map': [(0, -43.2), (1, 43.2)], 'rest': -52},
        {'signal': 'speed', 'c': [745, 763], 'r': 238, 'cut': 860, 'pivot': [745, 763], 'hub': 33, 'tail': 50,
         'needle': [228, 9], 'map': [(0, -114), (20, -108), (250, 117.82)], 'rest': -114},
        {'signal': 'rpm', 'c': [1270, 763], 'r': 238, 'cut': 985, 'pivot': [1270, 763], 'hub': 33, 'tail': 50,
         'needle': [228, 9], 'map': TACH_ANG + [(7600, 125)], 'rest': -117},
        {'signal': 'coolant', 'c': [1657, 845], 'r': 132, 'pivot': [1658, 902], 'hub': 24, 'tail': 18, 'needle': [130, 7],
         'map': [(40, -49.6), (50, -38), (90, 0), (120, 41), (130, 49.6)], 'rest': -52},
    ],
    # [dial, first angle, last angle, count, outer radius, length, width]
    'ticks': [
        [1, -108, 108, 12, 234, 32, 9],                 # 20 .. 240 km/h
        [1, -98.18, 117.82, 12, 234, 20, 3.5],          # 30 .. 250
        [2, -116.6, -116.6, 1, 234, 26, 8],             # 0 rpm
        [2, -92, 116.6, 7, 234, 26, 8],                 # 1 .. 7
        [2, -104.3, -104.3, 1, 234, 22, 3],             # 500
        [2, -74.6, 99.2, 6, 234, 22, 3],                # 1500 .. 6500
        [0, -43.2, 43.2, 5, 138, 20, 4.5],              # 0 1/4 1/2 3/4 1/1
        [3, -49.6, 49.6, 4, 128, 18, 4.5],
    ],
    # [dial, from angle, to angle, inner radius, outer radius, colour(, stripes)]
    'zones': [
        [2, lerp_ang(TACH_ANG, 6300), 116.6, 199, 226, 'red'],
        [2, lerp_ang(TACH_ANG, 6020), lerp_ang(TACH_ANG, 6260), 205, 226, 'red', 3],   # three red stripes
        [0, -36, -24, 112, 140, 'red'],
        [3, -44, -32, 104, 132, 'blue'],
        [3, 35, 47, 104, 132, 'red'],
    ],
    # the printing: (text, font, photo centre x, y); '⅟' is the fuel gauge's "1/1" (tools/bake_fonts.py)
    'texts': [
        ('20', 'e_spd', 583, 818), ('40', 'e_spd', 570, 760), ('60', 'e_spd', 578, 703), ('80', 'e_spd', 602, 653),
        ('100', 'e_spd', 648, 613), ('120', 'e_spd', 706, 585), ('140', 'e_spd', 772, 578), ('160', 'e_spd', 828, 596),
        ('180', 'e_spd', 873, 635), ('200', 'e_spd', 902, 688), ('220', 'e_spd', 917, 743), ('240', 'e_spd', 911, 800),
        ('km/h', 'e_lab', 752, 675), ('EG', 'e_xs', 752, 696),
        ('0', 'e_rpm', 1099, 854), ('1', 'e_rpm', 1069, 764), ('2', 'e_rpm', 1112, 670), ('3', 'e_rpm', 1195, 607),
        ('4', 'e_rpm', 1306, 602), ('5', 'e_rpm', 1396, 654), ('6', 'e_rpm', 1447, 751), ('7', 'e_rpm', 1435, 854),
        ('1/min', 'e_lab', 1264, 665), ('x1000', 'e_lab', 1264, 690),
        ('0', 'e_lab', 1137, 888), ('10', 'e_lab', 1211, 930), ('20', 'e_lab', 1289, 933), ('30', 'e_lab', 1361, 896),
        ('L/100km', 'e_sm', 1249, 904),
        ('0', 'e_lab', 257, 763), ('½', 'e_frac', 350, 733), ('⅟', 'e_frac', 437, 770),
    ],
    # (icon, photo centre x, y, size)
    'icons': [('fuel', 352, 808, 48), ('e36cool', 1658, 848, 46)],
    'econ': {'pivot': [1250, 815], 'top': 877, 'len': 150, 'width': 4.5, 'ticks': EU_ECON_TICKS,
             'values': list(range(0, 31, 2)), 'rest': -118},
}



# --- the mph (US) face, us-mph-day-face.png (1600 x 1200) --------------------------------------------------------
# The same housing as the EU face: only the speedometer's scales, the economy gauge (MPG), the printing and the
# fuel reserve block (orange) differ. Its own measurements are taken relative to their dial's pivot in the US photo
# and carried into the EU photo's frame (k: the two photos' scale, from the hubs' distance, 525 / 442 px).
US_K = 525 / 442
US_PIVOT = {'fuel': (256, 893), 'spd': (583, 762), 'tach': (1025, 771), 'cool': (1365, 895)}
EU_PIVOT = {'fuel': (338, 902), 'spd': (745, 763), 'tach': (1270, 763), 'cool': (1658, 902)}


def us2eu(dial, x, y):
    (ux, uy), (ex, ey) = US_PIVOT[dial], EU_PIVOT[dial]
    return ex + (x - ux) * US_K, ey + (y - uy) * US_K


def mph_ang(v):
    """The outer MPH scale: 16.2 degrees a 10 mph, 20 mph at -102.3."""
    return -102.3 + 1.6225 * (v - 20)


US_ECON_TICKS = [   # (outer end, inner end) in the US photo, width, MPG (None: the wedges past 40, not on the map)
    ((885, 900), (912.5, 882.5), 10, None), ((905, 912.5), (927.5, 895), 10, None),
    ((931, 927.5), (952.5, 905), 4, 40), ((971, 930), (977.5, 914), 3.5, 25), ((992.5, 931), (996, 917.5), 3.5, 20),
    ((1025, 931), (1026, 919), 3.5, 15), ((1102.5, 930), (1082.5, 907.5), 4, 10), ((1155, 897.5), (1126, 878.5), 5, 8),
]
US = copy.deepcopy(EU)
US.update({
    'photo': 'us-mph-day-face.png',
    'mph': True,
})
US['dials'][1]['map'] = [(0, -121), (20, mph_ang(20)), (150, mph_ang(150))]
US['dials'][1]['rest'] = -121
US['ticks'] = [
    [1, mph_ang(10), mph_ang(150), 15, 228, 28.5, 8.3],                 # 10 .. 150 mph
    [1, mph_ang(15), mph_ang(145), 14, 228, 16.6, 3.5],                 # 15 .. 145
    [1, mph_ang(20 * 0.621371), mph_ang(240 * 0.621371), 23, 147, 10.7, 3],   # the inner km/h ring, 20 .. 240 every 10
] + [t for t in EU['ticks'] if t[0] != 1]
US['zones'] = [z if z[0] != 0 else [0, -41, -29, 112, 140, 'orange'] for z in EU['zones']]
_ep = us2eu('tach', 1035.5, 818)
US['econ'] = {'pivot': [round(_ep[0], 1), round(_ep[1], 1)], 'top': round(us2eu('tach', 0, 861)[1], 1), 'len': 150,
              'width': 4.5, 'rest': -113,
              'ticks': [(us2eu('tach', *o), us2eu('tach', *i), w * US_K) for o, i, w, v in US_ECON_TICKS],
              'values': [v for o, i, w, v in US_ECON_TICKS]}
_US_TEXTS = [   # (text, font, dial, US photo centre x, y)
    ('20', 'e_spd', 'spd', 441.5, 797), ('40', 'e_spd', 'spd', 445, 716), ('60', 'e_spd', 'spd', 493.5, 652),
    ('80', 'e_spd', 'spd', 571.5, 616), ('100', 'e_spd', 'spd', 656, 633.5), ('120', 'e_spd', 'spd', 713, 687.5),
    ('140', 'e_spd', 'spd', 736, 767.5),
    ('20', 'e_lab', 'spd', 500, 802), ('40', 'e_lab', 'spd', 495, 772), ('60', 'e_lab', 'spd', 497.5, 742),
    ('80', 'e_lab', 'spd', 510, 716), ('100', 'e_lab', 'spd', 534, 692), ('120', 'e_lab', 'spd', 564, 676),
    ('140', 'e_lab', 'spd', 595, 671), ('160', 'e_lab', 'spd', 629, 682), ('180', 'e_lab', 'spd', 655, 702),
    ('200', 'e_lab', 'spd', 669, 730), ('220', 'e_lab', 'spd', 678.5, 760), ('240', 'e_lab', 'spd', 675, 789),
    ('km/h', 'e_sm', 'spd', 587, 714), ('MPH', 'e_lab', 'spd', 589, 825), ('EG', 'e_xs', 'spd', 589, 842),
    ('MPG', 'e_sm', 'tach', 1017, 879.5), ('40', 'e_us', 'tach', 955, 891), ('25', 'e_us', 'tach', 979, 900),
    ('20', 'e_us', 'tach', 1002, 904), ('15', 'e_us', 'tach', 1026, 904), ('10', 'e_us', 'tach', 1076, 892),
    ('8', 'e_us', 'tach', 1112, 871),
    ('0', 'e_lab', 'fuel', 176, 791), ('½', 'e_frac', 'fuel', 255, 762), ('⅟', 'e_frac', 'fuel', 330, 792),
    ('UNLEADED GASOLINE', 'e_word', 'fuel', 255, 851), ('ONLY', 'e_word', 'fuel', 255, 934),
]
_EU_TACH_TEXTS = [t for t in EU['texts'] if t[1] == 'e_rpm' or t[0] in ('1/min', 'x1000')]
US['texts'] = _EU_TACH_TEXTS + [(t, f) + tuple(round(v, 1) for v in us2eu(d, x, y)) for t, f, d, x, y in _US_TEXTS]
US['icons'] = [('fuel',) + tuple(round(v, 1) for v in us2eu('fuel', 260, 821)) + (40,),
               ('e36cool',) + tuple(round(v, 1) for v in us2eu('cool', 1361, 830)) + (46,)]

def place(face):
    """Scale and offset from the face photo to the cluster: true proportions, the lamp strips' bottom at y 718."""
    s = 0.9
    strip_bottom = max(y + h for _, y, _, h in face['strips'])
    box = face['face']['box']
    ox = W / 2 - s * (box[0] + box[2]) / 2
    oy = 718 - s * strip_bottom
    return s, ox, oy


def build(face, wid, toggle):
    s, ox, oy = place(face)
    X = lambda x: round(ox + s * x, 1)
    Y = lambda y: round(oy + s * y, 1)
    L = lambda v: round(s * v, 2)
    F = face['face']
    dials = []
    for d in face['dials']:
        out = {'signal': d['signal'], 'c': [X(d['c'][0]), Y(d['c'][1])], 'r': L(d['r']), 'cut': Y(d['cut']) if d.get('cut') else 0,
               'pivot': [X(d['pivot'][0]), Y(d['pivot'][1])], 'hub': L(d['hub']), 'tail': L(d['tail']),
               'needle': [L(d['needle'][0]), L(d['needle'][1])], 'map': [[v, round(a, 2)] for v, a in d['map']],
               'rest': d['rest']}
        dials.append(out)
    E = face['econ']
    px, py = E['pivot']
    eticks, emap = [], []
    for ((x0, y0), (x1, y1), w), v in zip(E['ticks'], E['values']):
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        ang = math.degrees(math.atan2(mx - px, -(my - py)))
        if eticks and ang - eticks[-1][0] > 180:     # the ticks point down past 6 o'clock: keep the angles continuous
            ang -= 360
        elif eticks and eticks[-1][0] - ang > 180:
            ang += 360
        r0, r1 = math.hypot(x0 - px, y0 - py), math.hypot(x1 - px, y1 - py)
        eticks.append([round(ang, 2), L(max(r0, r1)), L(min(r0, r1)), L(w)])
        if v is not None:
            emap.append([v, round(ang, 2)])
    emap.sort(key=lambda e: e[0])
    tach = face['dials'][2]
    dash = {
        'id': wid, 'type': 'e36dash', 'class': 'content', 'z': 0, 'x': 0, 'y': 0, 'w': W, 'h': ROW,
        'toggle': toggle, 'mph': face['mph'],
        'face': {'box': [X(F['box'][0]), Y(F['box'][1]), X(F['box'][2]), Y(F['box'][3])], 'radius': L(F['radius']),
                 'arch': [X(F['arch'][0]), Y(F['arch'][1]), L(F['arch'][2])], 'bezel': L(F['bezel'])},
        'dials': dials,
        'ticks': [[g[0], g[1], g[2], g[3], L(g[4]), L(g[5]), L(g[6])] for g in face['ticks']],
        'zones': [[z[0], round(z[1], 2), round(z[2], 2), L(z[3]), L(z[4]), z[5], z[6] if len(z) > 6 else 0] for z in face['zones']],
        'windows': [[X(x), Y(y), L(w), L(h), L(r)] for x, y, w, h, r in face['windows']],
        'strips': [[X(x), Y(y), L(w), L(h)] for x, y, w, h in face['strips']], 'stripR': L(face['stripR']),
        'arrows': [[X(x), Y(y), L(sz), d] for x, y, sz, d in face['arrows']],
        'knob': [X(face['knob'][0]), Y(face['knob'][1]), L(face['knob'][2])],
        'sensor': [X(face['sensor'][0]), Y(face['sensor'][1]), L(face['sensor'][2])],
    }
    # the economy gauge's own layer: the rev counter's circle below the window's top line
    cx, cy, r = X(tach['c'][0]), Y(tach['c'][1]), L(tach['r'])
    top = Y(E['top'])
    half = math.sqrt(max(0.0, r * r - (top - cy) ** 2))
    ex0, ex1 = math.floor(cx - half) - 2, math.ceil(cx + half) + 2
    ey0, ey1 = math.floor(top) - 3, min(ROW, math.ceil(Y(tach['cut']) if tach.get('cut') else cy + r))
    econ = {
        'id': wid.replace('dash', 'econ'), 'type': 'e36econ', 'class': 'content', 'z': 0,
        'x': ex0, 'y': ey0, 'w': ex1 - ex0, 'h': ey1 - ey0, 'toggle': toggle, 'mph': face['mph'],
        'tach': [cx, cy, r],
        'econ': {'pivot': [X(px), Y(py)], 'top': top, 'len': L(E['len']), 'width': L(E['width']),
                 'ticks': eticks, 'map': emap, 'rest': E['rest']},
    }
    tag = wid.split('_')[1]
    texts = [text_widget('t%s_%d' % (tag, i), t, fn, X(x), Y(y), toggle) for i, (t, fn, x, y) in enumerate(face['texts'])]
    icons = [{'id': 'i%s_%s' % (tag, name), 'type': 'icon', 'icon': name, 'class': 'content', 'z': 5,
              'x': round(X(x) - L(sz) / 2), 'y': round(Y(y) - L(sz) / 2), 'w': round(L(sz)), 'h': round(L(sz)),
              'color': 'mark', 'toggle': toggle} for name, x, y, sz in face['icons']]
    return [dash, econ] + texts + icons


def layout():
    widgets = build(EU, 'dash_eu', 'units=metric') + build(US, 'dash_us', 'units=us')
    return {
        'schemaVersion': 2,
        'name': 'E36',
        'packWaste': 3,
        'theme': 'e36',
        '_about': 'E36 cluster, generated by tools/gen_e36.py (edit that and regenerate): the BMW E36 328i cluster of the 90s, '
                  'traced off face-on photos at true proportions. The EU face (km/h, L/100km) with metric units, the US face '
                  '(MPH, MPG) with US units. One e36dash shader draws the face, dials, ticks, zones and needles; the printed '
                  'figures are text widgets. Lamps and turn arrows are never lit (the app cannot read them). BMW\'s gear letter '
                  'shows through the right lamp strip. Widget reference: shared/hud.js header.',
        'widgets': widgets,
    }


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else 'apps/cluster_themes/hud/layouts/e36.json'
    with open(out, 'w') as f:
        json.dump(layout(), f, indent=2)
        f.write('\n')
    print('wrote', out)
