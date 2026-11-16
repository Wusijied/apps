'use strict';
/**
 * The E36 theme's needle and economy maths (Cluster Themes "e36", widget e36dash in hud.js).
 *
 * The E36 328i cluster's needles read off printed scales, some of them non-linear (the economy gauge), so every dial
 * carries a table of [value, fraction of the sweep] pairs traced off the photos (tools/gen_e36.py) and frac() reads
 * the needle's place off it. The car has no fuel-flow signal, so the economy gauge is estimated from the engine's
 * power: flow = power x 250 g/kWh (a petrol engine's brake-specific fuel consumption near its best) / 745 g/L, never
 * under an idle floor of 0.8 L/h.
 *
 * Plain Node 8 (the car's 8.16.2): no optional chaining, no ??, no dependencies.
 */

const BSFC_G_PER_KWH = 250;      // grams of fuel per kWh, a petrol engine near its best
const PETROL_G_PER_L = 745;      // grams in a litre of petrol
const IDLE_LPH = 0.8;            // a 3-litre six at idle, warm
const STILL_KMH = 3;             // under this the car stands: the economy needle reads the thirsty end
const L100_PER_MPG = 235.215;    // L/100km x MPG (US) = 235.215
const TRIP_GAP_MS = 2000;        // a gap in the speed samples longer than this adds nothing to the trip

function isNum(v) { return typeof v === 'number' && !isNaN(v); }

/** Where the needle sits on a scale, 0..1, from `table` ([[value, frac], ...], values rising or falling); linear
 *  between the points and clamped to the scale's ends. No data (null, NaN) gives null: the caller parks the needle. */
function frac(value, table) {
    if (!isNum(value) || !table || !table.length) return null;
    const rising = table[table.length - 1][0] >= table[0][0];
    const at = (i) => table[rising ? i : table.length - 1 - i];
    if (value <= at(0)[0]) return at(0)[1];
    if (value >= at(table.length - 1)[0]) return at(table.length - 1)[1];
    for (let i = 1; i < table.length; i++) {
        const a = at(i - 1), b = at(i);
        if (value <= b[0]) return b[0] === a[0] ? b[1] : a[1] + (b[1] - a[1]) * (value - a[0]) / (b[0] - a[0]);
    }
    return at(table.length - 1)[1];
}

/** The engine's fuel flow in L/h from its power in kW (estimated, see the header); null without power. */
function flowLph(powerKw) {
    if (!isNum(powerKw)) return null;
    return Math.max(IDLE_LPH, Math.max(0, powerKw) * BSFC_G_PER_KWH / PETROL_G_PER_L);
}

/** What the economy gauge reads: L/100km (us false) or US MPG (us true). Standing still (under 3 km/h) it reads the
 *  thirsty end: Infinity L/100km, 0 MPG. Null without data. */
function economy(speedKmh, flow, us) {
    if (!isNum(speedKmh) || !isNum(flow)) return null;
    if (speedKmh < STILL_KMH) return us ? 0 : Infinity;
    const l100 = flow / speedKmh * 100;
    return us ? L100_PER_MPG / l100 : l100;
}

/** Exponential smoothing with time constant `ms`. The first value (and the first after an infinite one) is taken as
 *  is; null holds the last value. */
class Smooth {
    constructor(ms) { this.ms = ms; this.v = null; this.at = 0; }

    step(v, now) {
        if (!isNum(v)) return this.v;
        if (!isNum(this.v) || !isFinite(this.v) || !isFinite(v)) {
            this.v = v;
        } else {
            const k = 1 - Math.exp(-Math.max(0, now - this.at) / this.ms);
            this.v += (v - this.v) * k;
        }
        this.at = now;
        return this.v;
    }
}

/** The trip counter: km driven since it was made, from speed samples. */
class Trip {
    constructor() { this.dist = 0; this.last = null; }

    /** A speed sample (km/h) at `now` ms. A gap over 2 s, or no speed, adds nothing. */
    add(speedKmh, now) {
        const prev = this.last;
        this.last = isNum(speedKmh) ? { v: Math.max(0, speedKmh), at: now } : null;
        if (!prev || !this.last) return;
        const dt = now - prev.at;
        if (dt <= 0 || dt > TRIP_GAP_MS) return;
        this.dist += (prev.v + this.last.v) / 2 * dt / 3600000;
    }

    km() { return this.dist; }
}

module.exports = { frac, flowLph, economy, Smooth, Trip };
