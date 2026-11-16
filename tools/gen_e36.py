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
import json
import math
import sys

W, H, ROW = 1920, 720, 660           # the cluster; BMW's strip row is y 660..720
GEAR = (1380, 1460)                  # BMW's gear letter shows through here, in the strip row


def lerp_ang(table, v):
    """The angle at value v on a [(value, angle)] scale (rising values)."""
    for (a, x), (b, y) in zip(table, table[1:]):
        if a <= v <= b:
            return x + (y - x) * (v - a) / (b - a)
    raise ValueError(v)


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
    'econ': {'pivot': [1250, 815], 'top': 877, 'len': 150, 'width': 4.5, 'ticks': EU_ECON_TICKS,
             'values': list(range(0, 31, 2)), 'rest': -118},
}


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
    return [dash, econ]


def layout():
    widgets = build(EU, 'dash_eu', 'units=metric')
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
