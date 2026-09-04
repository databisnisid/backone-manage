import type * as gmaps from "google.maps";

declare global {
  // google.maps namespace types pulled in for the map page
  namespace google {
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    type Map = gmaps.Map;
    type Marker = gmaps.Marker;
    type Circle = gmaps.Circle;
    type LatLngLiteral = gmaps.LatLngLiteral;
    const SymbolPath: typeof gmaps.SymbolPath;
  }
}

export {};