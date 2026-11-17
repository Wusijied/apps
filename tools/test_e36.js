'use strict';
/**
 * Tests for the E36 cluster theme (Cluster Themes "e36"): the needle and economy maths in shared/e36.js, the
 * night colours, and the generated layout. Plain Node with assert, no dependencies:
 *
 *     node tools/test_e36.js
 */
const assert = require('assert');
const fs = require('fs');
const path = require('path');

let failed = 0, passed = 0;
function test(name, fn) {
    try {
        fn();
        passed++;
    } catch (e) {
        failed++;
        console.log('FAIL ' + name + '\n  ' + (e && e.message || e));
    }
}
const near = (a, b, eps) => Math.abs(a - b) <= eps;

const e36 = require('../shared/e36');

// --- needle maths -------------------------------------------------------------------------------------------------
test('frac: linear between the ends', () => {
    const t = [[20, 0], [240, 1]];
    assert.strictEqual(e36.frac(130, t), 0.5);
});
test('frac: clamps below and above the scale', () => {
    const t = [[20, 0], [240, 1]];
    assert.strictEqual(e36.frac(5, t), 0);
    assert.strictEqual(e36.frac(300, t), 1);
    assert.strictEqual(e36.frac(-12, t), 0);
});
test('frac: no data gives null (the needle parks)', () => {
    const t = [[20, 0], [240, 1]];
    assert.strictEqual(e36.frac(null, t), null);
    assert.strictEqual(e36.frac(undefined, t), null);
    assert.strictEqual(e36.frac(NaN, t), null);
});
test('frac: a descending table (the MPG face runs 40 -> 8)', () => {
    assert.strictEqual(e36.frac(10, [[40, 0], [8, 1]]), 0.9375);
    assert.strictEqual(e36.frac(Infinity, [[40, 0], [8, 1]]), 0);
});
test('frac: piecewise, a non-linear scale', () => {
    const t = [[50, 0], [90, 0.5], [120, 1]];
    assert.strictEqual(e36.frac(70, t), 0.25);
    assert.strictEqual(e36.frac(105, t), 0.75);
    assert.strictEqual(e36.frac(135, t), 1);
});

// --- economy -------------------------------------------------------------------------------------------------------
test('flowLph: idle floor and full power', () => {
    assert.strictEqual(e36.flowLph(0), 0.8);
    assert.ok(near(e36.flowLph(100), 33.56, 0.01), String(e36.flowLph(100)));
    assert.strictEqual(e36.flowLph(null), null);
});
test('economy: L/100km and MPG', () => {
    assert.strictEqual(e36.economy(100, 8, false), 8);
    assert.ok(near(e36.economy(100, 8, true), 29.4, 0.01), String(e36.economy(100, 8, true)));
});
test('economy: standing still reads the thirsty end (the EU face\'s 30, finite so the needle eases)', () => {
    assert.strictEqual(e36.economy(1, 0.8, false), 30);
    assert.strictEqual(e36.economy(2, 0.8, true), 0);
    assert.strictEqual(e36.economy(0, 0.8, false), 30);
    assert.strictEqual(e36.economy(4, 2, false), 30);          // 50 L/100km: past the face's end
});
test('economy: creeping at 2..4 km/h moves the needle smoothly, no 15 degree jumps', () => {
    const s = new e36.Smooth(1000);
    const vals = [2, 3.2, 2.5, 3.5, 2.8].map((kmh, i) => s.step(e36.economy(kmh, 0.8, false), i * 50));
    vals.forEach((v) => assert.ok(isFinite(v) && v > 26 && v <= 30, String(v)));
});
test('economy: no data gives null', () => {
    assert.strictEqual(e36.economy(null, 8, false), null);
    assert.strictEqual(e36.economy(50, null, true), null);
});

// --- smoothing and the trip readout ------------------------------------------------------------------------------------------
test('Smooth: first value taken as is, then eases', () => {
    const s = new e36.Smooth(1000);
    assert.strictEqual(s.step(10, 0), 10);
    const v = s.step(20, 1000);
    assert.ok(v > 15 && v < 20, String(v));
});
test('Smooth: no data drops the value (the needle parks), and the next value starts fresh', () => {
    const s = new e36.Smooth(1000);
    s.step(10, 0);
    assert.strictEqual(s.step(null, 500), null);
    assert.strictEqual(s.step(25, 1000), 25);
});
test('Smooth: Infinity in or out does not poison it', () => {
    const s = new e36.Smooth(1000);
    s.step(10, 0);
    const v = s.step(Infinity, 500);
    assert.strictEqual(v, Infinity);
    const w = s.step(12, 1000);
    assert.ok(isFinite(w), String(w));
});
test('tripText: the E36 trip reads 000.0, in km or miles, and rolls over at 1000', () => {
    assert.strictEqual(e36.tripText(0, false), '000.0');
    assert.strictEqual(e36.tripText(12.34, false), '012.3');
    assert.strictEqual(e36.tripText(1.609344, true), '001.0');
    assert.strictEqual(e36.tripText(1000.5, false), '000.5');
    assert.strictEqual(e36.tripText(null, false), '000.0');
});

// --- night colours ------------------------------------------------------------------------------------------------
const themes = require('../shared/hud_themes');
test('nightTheme: a theme with night roles takes them', () => {
    const t = themes.nightTheme(themes.THEMES.e36, 0.6);
    assert.deepStrictEqual(t.mark, themes.THEMES.e36.night.mark);
    assert.deepStrictEqual(t.lcd, themes.THEMES.e36.night.lcd);
    assert.strictEqual(t.night, undefined);
    assert.strictEqual(t.name, 'E36');
});
test('nightTheme: other themes still dim their whites and greys to 60 %', () => {
    const t = themes.nightTheme(themes.THEMES.classic, 0.6);
    assert.deepStrictEqual(t.fg, [146, 148, 150, 255]);
    assert.deepStrictEqual(t.bar, themes.THEMES.classic.bar);
});
test('E36 palette: every role the layout uses exists by day and by night', () => {
    const roles = ['bg', 'bezel', 'face', 'dial', 'mark', 'needle', 'hub', 'red', 'blue', 'orange', 'arrow', 'well',
        'lcd', 'strip', 'fg', 'dim'];
    roles.forEach((r) => {
        assert.ok(Array.isArray(themes.THEMES.e36[r]), 'day ' + r);
        assert.ok(Array.isArray(themes.nightTheme(themes.THEMES.e36, 0.6)[r]), 'night ' + r);
    });
    assert.strictEqual(themes.THEMES.e36.noGarland, true);
});

// --- shipping ------------------------------------------------------------------------------------------------------
test('shared/hud.js: every shared file it requires at load is in the "shared" list of each app that ships it', () => {
    const src = fs.readFileSync(path.join(__dirname, '..', 'shared', 'hud.js'), 'utf8');
    const need = [];
    // the top-level requires (a lazy one inside a method, like the nav widget's, loads only where it is used)
    src.replace(/^const [^=]+= require\('\.\/([a-z_0-9]+)(\.js)?'\)/gm, (m, n) => { need.push(n + '.js'); return m; });
    ['cluster_themes', 'idrive_hud_widgets'].forEach((app) => {
        const spec = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'apps', app, 'app.json'), 'utf8'));
        if (spec.shared.indexOf('hud.js') < 0) return;
        const missing = need.filter((f) => spec.shared.indexOf(f) < 0);
        assert.deepStrictEqual(missing, [], app);
    });
});

// --- the generated layout ------------------------------------------------------------------------------------------
const os = require('os');
const LAYOUT = path.join(__dirname, '..', 'apps', 'cluster_themes', 'hud', 'layouts', 'e36.json');
const loadLayout = () => JSON.parse(fs.readFileSync(LAYOUT, 'utf8'));
const overlaps = (w, r) => w.x < r[2] && w.x + w.w > r[0] && w.y < r[3] && w.y + w.h > r[1];
test('layout: valid for the 1920x720 cluster', () => {
    // shared/hud_data.js opens the build's packed hud/ (kit/pack, only there in a build); validation never reads it
    const hd = path.join(__dirname, '..', 'shared', 'hud_data.js');
    require.cache[hd] = { id: hd, filename: hd, loaded: true, exports: { json: () => ({}) } };
    const Layouts = require('../shared/layouts');
    const L = new Layouts(fs.mkdtempSync(path.join(os.tmpdir(), 'e36-')), { warn() {}, info() {}, error() {} }, [1920, 720]);
    L._validate(loadLayout(), 'e36');
});
test('layout: only the backdrop pieces reach under the hood or the belt light', () => {
    const warns = require('../shared/visible').check(loadLayout().widgets, 'panel');
    const bad = warns.filter((s) => !/^(dash|strip_|needles_)/.test(s));     // the needles' layer: see-through
    assert.deepStrictEqual(bad, []);
});
test('layout: BMW\'s bottom row stays open (its range, clock, gear letter and outside temperature show there)', () => {
    const over = loadLayout().widgets.filter((w) => overlaps(w, [0, 660, 1920, 720])).map((w) => w.id);
    assert.deepStrictEqual(over, []);
});
test('layout: the LCD shows only distances (the range and the trip), one row as on the car', () => {
    const lcd = loadLayout().widgets.filter((w) => /^l(eu|us)_/.test(w.id)).map((w) => w.text);
    assert.ok(lcd.length > 0);
    lcd.forEach((t) => assert.ok(!/time|ampm|ambient|temp/.test(t), t));
});
test('layout: each face has its e36dash, on its own units and redlines (the M3 on the 0 .. 8 rev counter)', () => {
    const ws = loadLayout().widgets.filter((w) => w.type === 'e36dash' && w.y === 0);
    const M3 = 'redline=7000|7500';
    const want = { 'units=metric&!': [false, false], 'units=us&!': [true, false], 'units=metric&': [false, true], 'units=us&': [true, true] };
    Object.keys(want).forEach((k) => {
        const [mph, m3] = want[k], w = ws.find((d) => d.toggle === k + M3);
        assert.ok(w, k + M3);
        assert.strictEqual(!!w.mph, mph, w.id);
        const nd = loadLayout().widgets.find((e) => e.type === 'e36needles' && e.toggle === w.toggle);
        assert.strictEqual(nd.needleColor, m3 ? 'mneedle' : undefined, w.id + ': red needles on the M3 only');
        assert.strictEqual(nd.econ.signal, m3 ? 'oil' : undefined, w.id + ': the oil gauge on the M3, economy on the 328i');
    });
    assert.strictEqual(ws.length, 4);
});
test('layout: the needles lie on top: over the print, the icons and the economy gauge (one layer a face, last)', () => {
    const ws = loadLayout().widgets;
    ws.filter((w) => w.type === 'e36dash' && w.y === 0).forEach((d) => {
        const mine = ws.filter((w) => w.toggle === d.toggle);
        const nd = mine.filter((w) => w.type === 'e36needles');
        assert.strictEqual(nd.length, 1, d.id);
        const top = Math.max.apply(null, mine.filter((w) => w !== nd[0]).map((w) => w.z || 0));
        assert.ok(nd[0].z > top, d.id + ': needles z ' + nd[0].z + ' over ' + top);
        assert.ok(nd[0].y + nd[0].h <= 660, d.id + ': above BMW\'s bottom row');
        // every needle within the layer at its full reach
        nd[0].dials.forEach((n) => {
            const k = Math.max(n.needle[0], n.tail, n.hub);
            assert.ok(n.pivot[0] - k >= nd[0].x && n.pivot[0] + k <= nd[0].x + nd[0].w && n.pivot[1] - k >= nd[0].y, d.id + ' ' + n.signal);
        });
        assert.ok(!d.dials.some((x) => x.needle), d.id + ': the face draws no needles');
        assert.strictEqual(ws.find((w) => w.type === 'e36econ' && w.toggle === d.toggle).econ.map, undefined, d.id + ': nor the economy layer');
    });
});
test('layout: the EU economy gauge is symmetric under the rev counter (window, ticks, needle pivot, print)', () => {
    const ws = loadLayout().widgets, ec = ws.find((w) => w.id === 'econ_eu'), nd = ws.find((w) => w.id === 'needles_eu');
    const ax = ec.tach[0], E = ec.econ;
    assert.ok(near(ax - E.cham[0], E.cham[2] - ax, 0.15) && E.cham[1] === E.cham[3], 'window corners and slopes: ' + E.cham);
    const T = E.ticks;
    T.forEach((t, i) => {
        const m = T[T.length - 1 - i];
        assert.ok(near(t[0] - ax, ax - m[0], 0.15) && near(t[1], m[1], 0.15), 'tick ' + i + ' mirrors ' + (T.length - 1 - i));
    });
    assert.ok(near(nd.econ.pivot[0], ax, 0.15), 'needle pivot on the axis');
    const t = (txt) => ws.find((w) => w.id.indexOf('teu_') === 0 && w.text === txt && w.x > ax - 300 && w.x < ax + 300);
    [['0', '30'], ['10', '20']].forEach(([a, b]) => {
        const A = t(a), B = t(b);
        assert.ok(near(ax - (A.x + A.w / 2), B.x + B.w / 2 - ax, 1) && A.y === B.y, a + ' / ' + b);
    });
});
test('layout: no trip knob or light sensor (redundant on a screen)', () => {
    loadLayout().widgets.filter((w) => w.type === 'e36dash').forEach((w) => {
        assert.strictEqual(w.knob, undefined, w.id);
        assert.strictEqual(w.sensor, undefined, w.id);
    });
});
test('layout: the M3 faces: 280 km/h, 170 MPH, the oil scale, the /M badge', () => {
    const ws = loadLayout().widgets, by = (id) => ws.find((w) => w.id === id);
    assert.deepStrictEqual(by('needles_eum3').dials[1].map.slice(-1)[0][0], 280);
    assert.deepStrictEqual(by('needles_usm3').dials[1].map.slice(-1)[0][0], 170);
    const oil = (id) => by(id).econ.map.map((e) => e[0]);
    assert.deepStrictEqual(oil('needles_eum3'), [40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150]);
    assert.deepStrictEqual(oil('needles_usm3'), [104, 120, 138, 156, 174, 192, 210, 228, 246, 264, 282, 300]);
    ['eum3', 'usm3'].forEach((t) => {
        const angs = by('needles_' + t).econ.map.map((e) => e[1]);
        angs.slice(1).forEach((a, i) => assert.ok(a < angs[i], t + ': the needle turns one way up the scale'));
        assert.ok(by('i' + t + '_e36m'), t + ': /M badge');
        assert.ok(by('i' + t + '_e36oil'), t + ': oil mark');
    });
    const figs = (t) => ws.filter((w) => w.id.indexOf('f' + t + '_') === 0).map((w) => w.text);
    assert.deepStrictEqual(figs('eum3'), Array.from({ length: 14 }, (_, k) => String(20 * (k + 1))));
    assert.ok(!ws.some((w) => /^t(eu|us)m3_/.test(w.id) && /L\/100km|MPG/.test(w.text)), 'no economy print on the M3');
});
test('toggles: "a&b" holds only while both parts do (hud.js _toggleOn)', () => {
    const hd = path.join(__dirname, '..', 'shared', 'hud_data.js');
    require.cache[hd] = require.cache[hd] || { id: hd, filename: hd, loaded: true, exports: { json: () => ({}) } };
    // hud.js loads the kit's modules, only there in a build: stand-ins (only _toggleOn is called)
    const Module = require('module'), load = Module._load;
    Module._load = function (req, parent) { return /^\.\/kit\//.test(req) ? {} : load.apply(this, arguments); };
    let Hud;
    try { Hud = require('../shared/hud'); } finally { Module._load = load; }
    const h = Object.create(Hud.prototype);
    const set = { units: 'us', redline: 7000, mapUp: false };
    h.setting = (k) => set[k];
    assert.strictEqual(h._toggleOn('units=us&redline=7000|7500'), true);
    assert.strictEqual(h._toggleOn('units=us&!redline=7000|7500'), false);
    assert.strictEqual(h._toggleOn('units=metric&redline=7000|7500'), false);
    set.redline = 6500;
    assert.strictEqual(h._toggleOn('units=us&!redline=7000|7500'), true);
});
test('layout: a rev counter for every Redline step, and one set of its figures shown for each', () => {
    const steps = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'apps', 'cluster_themes', 'app.json'), 'utf8'))
        .settings.find((s) => s.key === 'redline').steps;
    const ws = loadLayout().widgets;
    const dashes = ws.filter((w) => w.type === 'e36dash' && w.y === 0);
    steps.forEach((r) => {
        // per units, exactly one face carries this redline's rev counter
        ['units=metric', 'units=us'].forEach((u) => {
            const has = dashes.filter((w) => w.toggle.indexOf(u + '&') === 0 && w.revs[r]);
            assert.strictEqual(has.length, 1, u + ' ' + r);
            const R = has[0].revs[r], N = ws.find((w) => w.type === 'e36needles' && w.toggle === has[0].toggle).revs[r];
            const top = N.map[N.map.length - 2][0];
            assert.ok(top > r, has[0].id + ' ' + r + ': the scale (' + top + ') runs past the redline');
            assert.ok(R.zones.some((z) => z[5] === 'red' && !z[6]), has[0].id + ' ' + r + ': a solid red zone');
        });
    });
    steps.forEach((r) => {
        const shown = ws.filter((w) => /^trev/.test(w.id) && w.toggle.slice(8).split('|').indexOf(String(r)) >= 0);
        const tops = Array.from(new Set(shown.map((w) => w.id.split('_')[0])));
        assert.strictEqual(tops.length, 1, r + ': one scale of figures, got ' + tops);
        const top = Number(tops[0].slice(4));
        assert.deepStrictEqual(shown.map((w) => w.text), Array.from({ length: top + 1 }, (_, k) => String(k)), String(r));
        const d = ws.find((w) => w.type === 'e36needles' && w.toggle.indexOf('units=metric&') === 0 && w.revs[r]);
        assert.strictEqual(top * 1000, d.revs[r].map.slice(-2)[0][0], r + ': figures match the needle\'s scale');
    });
});

if (failed) {
    console.log('e36: ' + failed + ' failed, ' + passed + ' passed');
    process.exit(1);
}
console.log('e36: all tests passed (' + passed + ')');
