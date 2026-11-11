/** Self-check for the Web-Mercator fit math. Run: node --experimental-strip-types frontend/utils/mapZoom.check.ts
 *
 *  Guards the property the flicker fix depends on: the returned zoom is the
 *  one that *just* contains the box, so no corrective listener is needed. */
import assert from "node:assert/strict";
import { zoomToFit } from "./mapZoom.ts";

const box = (a: [number, number], b: [number, number]) => ({
  ne: { lat: Math.max(a[0], b[0]), lng: Math.max(a[1], b[1]) },
  sw: { lat: Math.min(a[0], b[0]), lng: Math.min(a[1], b[1]) },
});

// Jakarta viewing a 4-member cluster spanning ~0.005 deg.
const jakarta = box([-6.175, 106.82], [-6.18, 106.825]);

// A degenerate box (all members jittered to one point) fits at any zoom; the
// caller's maxZoom cap is what stops it. Must not be NaN or negative.
const point = zoomToFit(box([-6.175, 106.82], [-6.175, 106.82]), 800, 600, 60);
assert.equal(point, Infinity, "degenerate box should report unbounded fit");

// Real box: finite, and wider boxes must need a lower zoom.
const wide = zoomToFit(box([-6.1, 106.7], [-6.3, 107.0]), 800, 600, 60);
const narrow = zoomToFit(jakarta, 800, 600, 60);
assert.ok(Number.isFinite(narrow) && narrow > 0, `narrow zoom not finite: ${narrow}`);
assert.ok(narrow > wide, `expected narrow(${narrow}) > wide(${wide})`);

assert.ok(
  zoomToFit(jakarta, 800, 600, 200) <= narrow,
  "more padding must not increase zoom",
);
const tall = zoomToFit(jakarta, 800, 4000, 60);
assert.ok(tall >= narrow, "extra height must not lower zoom");
const wideBox = box([-6.5, 106.0], [-5.8, 107.5]); // width-limited
assert.equal(
  zoomToFit(wideBox, 800, 600, 60),
  zoomToFit(wideBox, 800, 4000, 60),
  "width-limited box must ignore height entirely",
);
// Antimeridian: 179 -> -179 is a 2 deg box, not 358 deg.
const across = zoomToFit(box([0, 179], [0, -179]), 800, 600, 60);
const twoDeg = zoomToFit(box([0, 1], [0, -1]), 800, 600, 60);
assert.ok(Math.abs(across - twoDeg) < 1e-9, `antimeridian span wrong: ${across} vs ${twoDeg}`);

// Poles clamp instead of producing Infinity/NaN.
const polar = zoomToFit(box([-90, 0], [90, 10]), 800, 600, 60);
assert.ok(Number.isFinite(polar), `polar zoom not finite: ${polar}`);

console.log("mapZoom: all checks passed");
