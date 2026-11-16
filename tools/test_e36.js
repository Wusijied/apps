'use strict';
/**
 * Tests for the E36 cluster theme (Cluster Themes "e36"): the needle and economy maths in shared/e36.js, the
 * night colours, and the generated layout. Plain Node with assert, no dependencies:
 *
 *     node tools/test_e36.js
 */
const assert = require('assert');

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
test('economy: standing still reads the thirsty end', () => {
    assert.strictEqual(e36.economy(1, 0.8, false), Infinity);
    assert.strictEqual(e36.economy(2, 0.8, true), 0);
    assert.strictEqual(e36.economy(0, 0.8, false), Infinity);
});
test('economy: no data gives null', () => {
    assert.strictEqual(e36.economy(null, 8, false), null);
    assert.strictEqual(e36.economy(50, null, true), null);
});

// --- smoothing and trip ------------------------------------------------------------------------------------------
test('Smooth: first value taken as is, then eases, null holds', () => {
    const s = new e36.Smooth(1000);
    assert.strictEqual(s.step(10, 0), 10);
    const v = s.step(20, 1000);
    assert.ok(v > 15 && v < 20, String(v));
    assert.strictEqual(s.step(null, 1500), v);
});
test('Smooth: Infinity in or out does not poison it', () => {
    const s = new e36.Smooth(1000);
    s.step(10, 0);
    const v = s.step(Infinity, 500);
    assert.strictEqual(v, Infinity);
    const w = s.step(12, 1000);
    assert.ok(isFinite(w), String(w));
});
test('Trip: 100 km/h for 36 s is 1 km', () => {
    const t = new e36.Trip();
    for (let i = 0; i <= 36; i++) t.add(100, i * 1000);
    assert.ok(near(t.km(), 1, 0.01), String(t.km()));
});
test('Trip: a gap over 2 s adds nothing', () => {
    const t = new e36.Trip();
    t.add(100, 0);
    t.add(100, 5000);
    assert.strictEqual(t.km(), 0);
});
test('Trip: no speed adds nothing', () => {
    const t = new e36.Trip();
    t.add(null, 0);
    t.add(null, 1000);
    t.add(50, 2000);
    assert.strictEqual(t.km(), 0);
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

// --- the generated layout ------------------------------------------------------------------------------------------
const fs = require('fs');
const os = require('os');
const path = require('path');
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
    const bad = warns.filter((s) => !/^(dash|strip_)/.test(s));
    assert.deepStrictEqual(bad, []);
});
test('layout: BMW\'s gear letter stays uncovered', () => {
    const over = loadLayout().widgets.filter((w) => overlaps(w, [1380, 660, 1460, 720])).map((w) => w.id);
    assert.deepStrictEqual(over, []);
});
test('layout: each face has its e36dash, on its own units', () => {
    const ws = loadLayout().widgets.filter((w) => w.type === 'e36dash' && w.y === 0);
    assert.ok(ws.some((w) => w.toggle === 'units=metric' && !w.mph), 'metric face');
});

if (failed) {
    console.log('e36: ' + failed + ' failed, ' + passed + ' passed');
    process.exit(1);
}
console.log('e36: all tests passed (' + passed + ')');
