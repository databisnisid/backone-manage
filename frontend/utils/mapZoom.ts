/** Web-Mercator fit math, pure so it can be checked without a browser.
 *
 *  `map.fitBounds()` cannot be capped without flicker: it animates to the raw
 *  fit zoom, an `idle` listener then pins it back to `maxZoom`. Computing the
 *  target up front and calling `setCenter` + `setZoom` once has no animation
 *  to race.
 */

const TILE = 256;

export type LatLng = { lat: number; lng: number };

const rad = (d: number) => (d * Math.PI) / 180;
/** Mercator y, clamped at the poles where tan() diverges. */
const mercY = (lat: number) =>
  Math.log(Math.tan(Math.PI / 4 + rad(Math.max(-85, Math.min(85, lat))) / 2));

/** Curl a longitude span into (-180, 180], so a box across the antimeridian
 *  reads as narrow instead of nearly the whole globe. */
const lngSpan = (deg: number) => {
  const m = Math.abs(deg) % 360;
  return m > 180 ? 360 - m : m;
};

/** Highest zoom at which a `w`×`h` viewport with `pad` px of slack still
 *  contains the box. `Infinity` for a degenerate (single-point) box. */
export function zoomToFit(
  bounds: { ne: LatLng; sw: LatLng },
  w: number,
  h: number,
  pad: number,
): number {
  const spanX = rad(lngSpan(bounds.ne.lng - bounds.sw.lng));
  const spanY = Math.abs(mercY(bounds.ne.lat) - mercY(bounds.sw.lat));
  const availW = Math.max(1, w - pad * 2);
  const availH = Math.max(1, h - pad * 2);
  const zX = spanX > 0 ? Math.log2((availW * 2 * Math.PI) / (TILE * spanX)) : Infinity;
  const zY = spanY > 0 ? Math.log2((availH * 2 * Math.PI) / (TILE * spanY)) : Infinity;
  return Math.min(zX, zY);
}
