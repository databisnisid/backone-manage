<template>
  <div class="relative h-full">
    <div
      v-if="!ready"
      class="absolute inset-x-4 top-4 z-10 rounded-lg border border-default bg-(--ui-bg) p-5 text-sm text-(--ui-text-dimmed) shadow-sm"
    >
      {{ mapError || "Loading map…" }}
    </div>
    <!-- V26: top-center keeps clear of Google's map-type (top-left) and
         fullscreen (top-right) controls, and of the banner above. -->
    <div v-if="ready && !single" class="absolute left-1/2 top-3 z-10 -translate-x-1/2">
      <UInput
        v-model="query"
        icon="i-lucide-search"
        placeholder="Search name, member ID, IP"
        size="sm"
        class="w-72 shadow-sm"
        :ui="{ base: 'bg-(--ui-bg)' }"
        @keydown.enter="applyNow"
        @keydown.esc="clearSearch"
        @focus="listOpen = true"
        @click="listOpen = true"
      />
    </div>
    <!-- Search result list: an overlay anchored under the input so the layout
         of the map never shifts. Capped height, scrolls past ~6 rows. Closed
         once a row is picked so it stops covering the pin it just panned to. -->
    <div
      v-if="ready && !single && listOpen && query.trim() && visible.length > 0"
      class="absolute left-1/2 top-16 z-10 max-h-64 w-72 -translate-x-1/2 overflow-y-auto rounded-lg border border-default bg-(--ui-bg) shadow-sm"
    >
      <button
        v-for="m in visible"
        :key="m.member_id"
        type="button"
        class="flex w-full items-center gap-2 border-b border-default px-3 py-2 text-left text-sm last:border-0 hover:bg-(--ui-bg-elevated)"
        :class="{ 'bg-(--ui-bg-elevated)': focusId === m.member_id }"
        @click="focusMember(m)"
      >
        <span
          class="size-2 shrink-0 rounded-full"
          :class="m.is_problem ? 'bg-red-500' : m.is_online ? 'bg-emerald-500' : 'bg-gray-400'"
        />
        <span class="min-w-0 flex-1 truncate">{{ m.name }}</span>
        <span class="shrink-0 font-mono text-xs text-(--ui-text-dimmed)">{{ m.ipaddress || "—" }}</span>
      </button>
    </div>
    <div
      v-if="ready && !single && query.trim() && visible.length === 0"
      class="absolute left-1/2 top-16 z-10 -translate-x-1/2 rounded-lg border border-default bg-(--ui-bg) px-3 py-2 text-sm text-(--ui-text-dimmed) shadow-sm"
    >
      No members match
    </div>
    <div
      ref="mapEl"
      class="w-full overflow-hidden rounded-lg border border-default shadow-sm"
      :class="height"
    ></div>
  </div>
</template>

<script setup lang="ts">
import type { Member, Route } from "~/types/api";
import { useBackendStore } from "~/stores/backend";
import logoSvgUrl from "~/assets/images/backone-logo.svg";
import { MarkerClusterer } from "@googlemaps/markerclusterer";
import { zoomToFit } from "~/utils/mapZoom";

const config = useRuntimeConfig();
const apiKey = config.public.googleMapsApiKey || "";
const mapEl = ref<HTMLElement | null>(null);
const ready = ref(false);
const mapError = ref("");

let map: google.maps.Map | null = null;
let markers: google.maps.Marker[] = [];
let flyers: google.maps.Circle[] = [];
let polylines: google.maps.Polyline[] = [];
let clusterer: MarkerClusterer | null = null;
let fitted = false; // fit the viewport to members once, then keep the user's view

/* ---- Search (V21/V22/V23/V25) ---- */

const query = ref("");
/** Whether the result list shows. Typing re-opens it; picking a row or Escape
 *  closes it, so the overlay never sits on the pin it just panned to. */
const listOpen = ref(true);
/** Last fetched members with coords, unfiltered (V23): the filter is a
 *  projection over this, never the source of truth, so clearing needs no refetch. */
let allMembers: (Member & { lat: number; lng: number })[] = [];
/** Members currently drawn — drives the "No members match" overlay (V22). */
const visible = ref<(Member & { lat: number; lng: number })[]>([]);

/** V25: null/undefined coerce to "" — `String(null)` is "null", which would
 *  otherwise match the query "null" against every un-IP'd member. */
function matches(m: Member, q: string): boolean {
  const needle = q.trim().toLowerCase();
  if (!needle) return true;
  return [m.name, m.member_id, m.ipaddress].some((v) =>
    String(v ?? "").toLowerCase().includes(needle),
  );
}

let debounceTimer: ReturnType<typeof setTimeout> | null = null;
/** Draw the current match set and fit the view to it (T13). Refresh-driven
 *  renders go through `renderMarkers()` alone so they keep the user's viewport. */
function applySearch() {
  renderMarkers();
  if (visible.value.length > 0) fitTo(visible.value);
}
/** Enter jumps to the top result instead of only re-fitting: with a short
 *  query the fit often covers the whole viewport, so name→pin needs a nudge. */
function applyNow() {
  if (debounceTimer) { clearTimeout(debounceTimer); debounceTimer = null; }
  renderMarkers();
  const first = visible.value[0];
  if (first) focusMember(first);
}
function clearSearch() {
  query.value = "";
  focusId.value = "";
  if (debounceTimer) { clearTimeout(debounceTimer); debounceTimer = null; }
  renderMarkers();
  if (visible.value.length > 0) fitTo(visible.value);
}
watch(query, () => {
  // A pick writes the member's name into the box itself and has already
  // rendered and moved the camera; a debounced fit here would undo its zoom,
  // and reopening the list would cover the pin it just framed.
  if (fromPick) { fromPick = false; return; }
  listOpen.value = true;
  if (debounceTimer) clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => { debounceTimer = null; applySearch(); }, 200);
});


const props = withDefaults(
  defineProps<{
    lat?: number | null;
    lng?: number | null;
    height?: string;
    zoom?: number;
    single?: boolean;
    members?: Member[];
    routes?: Route[];
    center?: { lat: number; lng: number };
  }>(),
  { lat: null, lng: null, height: "h-[600px]", zoom: 15, single: false },
);

/* ---- BackOne logo preload (canvas marker glyph) ---- */

const logoImg = new Image();
let logoReady = false;

const logoLoaded = new Promise<void>((resolve) => {
  logoImg.crossOrigin = "anonymous";
  logoImg.onload = () => { logoReady = true; resolve(); };
  logoImg.onerror = () => resolve();
  logoImg.src = logoSvgUrl;
});

/* ---- Marker icon builder (teardrop pin + logo via canvas) ---- */

const PIN_W = 36; // marker width in px, canvas below
function makeMarkerIcon(statusColor: string): google.maps.Icon {
  const W = PIN_W, H = 48;
  const canvas = document.createElement("canvas");
  canvas.width = W;
  canvas.height = H;
  const ctx = canvas.getContext("2d")!;

  // Pin body
  ctx.beginPath();
  ctx.moveTo(18, 0);
  ctx.bezierCurveTo(28, 0, 36, 10, 36, 16);
  ctx.bezierCurveTo(36, 32, 22, 48, 18, 48);
  ctx.bezierCurveTo(14, 48, 0, 32, 0, 16);
  ctx.bezierCurveTo(0, 10, 8, 0, 18, 0);
  ctx.closePath();
  ctx.fillStyle = statusColor;
  ctx.fill();

  // White circle backdrop for logo
  ctx.beginPath();
  ctx.arc(18, 16, 10, 0, Math.PI * 2);
  ctx.fillStyle = "#fff";
  ctx.fill();

  // BackOne logo glyph (if loaded)
  if (logoReady) {
    ctx.save();
    ctx.beginPath();
    ctx.arc(18, 16, 10, 0, Math.PI * 2);
    ctx.clip();
    const s = 20 / logoImg.naturalHeight;
    const lw = logoImg.naturalWidth * s;
    const lh = logoImg.naturalHeight * s;
    ctx.drawImage(logoImg, 18 - lw / 2, 16 - lh / 2, lw, lh);
    ctx.restore();
  }

  return { url: canvas.toDataURL(), anchor: new google.maps.Point(W / 2, H) };
}

/* ---- Add / refresh markers ---- */

/** Exact coords, no offset: the clusterer resolves overlaps. */
function addMemberMarker(m: {
  lat: number; lng: number; name: string; member_id: string; color: string;
}): google.maps.Marker {
  const marker = new google.maps.Marker({
    position: { lat: m.lat, lng: m.lng },
    title: m.name,
    icon: makeMarkerIcon(m.color),
  });
  if (m.member_id) {
    marker.addListener("click", () => {
      window.location.assign(`/members/${encodeURIComponent(m.member_id)}`);
    });
  }
  markers.push(marker);
  return marker;
}

/** Fetch latest members, refresh the cache, then re-render. The active query
 *  is re-applied here (V22) so a refresh never silently drops it. */
async function refreshMarkers() {
  if (!map) return;
  const members = props.members && props.members.length > 0
    ? props.members
    : await api<Member[]>("/api/app/members/");
  // V20: null check, not falsy — a coord of 0 is a real location.
  allMembers = members.filter(
    (m): m is Member & { lat: number; lng: number } => m.lat != null && m.lng != null,
  );
  renderMarkers();
  // Fit once, like the dashboard's calculateMapCenter: with a fixed center the
  // pins land off-screen. Later refreshes keep the user's viewport.
  if (!fitted && allMembers.length > 0) {
    fitted = true;
    fitTo(allMembers);
  }
}

/** Pure projection over the cache (V23): draws the current match set.
 *  Never fetches — clearing the search restores pins with no request. */
function renderMarkers() {
  if (!map) return;
  clusterer?.clearMarkers();
  markers.forEach((m) => m.setMap(null));
  flyers.forEach((f) => f.setMap(null));
  markers = [];
  flyers = [];

  const shown = allMembers.filter((m) => matches(m, query.value));
  visible.value = shown;

  const created: google.maps.Marker[] = [];
  for (const m of shown) {
    const color = m.is_problem ? "#dc2626" : m.is_online ? "#16a34a" : "#64748b";
    created.push(addMemberMarker({
      lat: m.lat, lng: m.lng, name: m.name, member_id: m.member_id, color,
    }));
    if (m.is_new) {
      flyers.push(new google.maps.Circle({
        map, center: { lat: m.lat, lng: m.lng }, radius: 150,
        strokeColor: "#0ea5e9", fillColor: "#0ea5e9", fillOpacity: 0.15,
      }));
    }
  }
  if (clusterer) {
    clusterer.addMarkers(created);
  } else {
    // Same effect as the dashboard map: nearby pins collapse into a count bubble.
    clusterer = new MarkerClusterer({ map, markers: created });
  }
}

/** Zoom used when a result is picked: deep enough that MarkerClusterer stops
 *  collapsing the pin into a count bubble. Separate from `mapZoom`, which caps
 *  a fit and is deliberately shallower. */
const PICK_ZOOM = 17;

/** Pan to a search result, promote it to the search query, and mark it
 *  selected. `panTo` is Google's native eased animation; the zoom is set first
 *  so the pan lands at the working zoom. Writing `query` re-renders, so only
 *  that member stays drawn — the box must not claim one name while every other
 *  pin is still on the map. */
const focusId = ref("");
let fromPick = false;
function focusMember(m: Member & { lat: number; lng: number }) {
  focusId.value = m.member_id;
  listOpen.value = false;
  if (query.value !== m.name) {
    fromPick = true; // the watcher must not queue a second, competing fit
    query.value = m.name;
  }
  renderMarkers();
  if (!map) return;
  map.setZoom(Math.max(map.getZoom() ?? 0, PICK_ZOOM));
  map.panTo({ lat: m.lat, lng: m.lng });
}

/** Recenter and set zoom in one shot, cap baked into the target (V24).
 *  `fitBounds` is unusable here: it animates to the raw fit zoom and a
 *  corrective `idle` listener then pins it back, which reads as zoom
 *  in → zoom out. Computing the target first means one camera move. */
function fitTo(list: { lat: number; lng: number }[]) {
  if (!map || list.length === 0) return;
  const maxZoom = Number(config.public.mapZoom) || 13;
  if (list.length === 1) {
    map.setCenter({ lat: list[0].lat, lng: list[0].lng });
    map.setZoom(maxZoom);
    return;
  }
  const ne = { lat: -90, lng: -180 };
  const sw = { lat: 90, lng: 180 };
  for (const m of list) {
    ne.lat = Math.max(ne.lat, m.lat); ne.lng = Math.max(ne.lng, m.lng);
    sw.lat = Math.min(sw.lat, m.lat); sw.lng = Math.min(sw.lng, m.lng);
  }
  map.setCenter({ lat: (ne.lat + sw.lat) / 2, lng: (ne.lng + sw.lng) / 2 });
  const w = mapEl.value?.clientWidth || 800;
  const h = mapEl.value?.clientHeight || 600;
  map.setZoom(Math.min(zoomToFit({ ne, sw }, w, h, 60), maxZoom));
}

/* ---- Route polylines ---- */
async function drawPolylines() {
  if (!map || !props.routes || props.routes.length === 0) return;
  polylines.forEach((p) => p.setMap(null));
  polylines = [];

  for (const r of props.routes) {
    const targetLoc = await fetchIpLoc(r.ip_network.split("/")[0]);
    const gwLoc = r.gateway ? await fetchIpLoc(r.gateway) : null;
    if (!targetLoc || !gwLoc) continue; // hide silently per §V.9

    const polyline = new google.maps.Polyline({
      path: [targetLoc, gwLoc],
      geodesic: true,
      strokeColor: "#f59e0b",
      strokeOpacity: 0.8,
      strokeWeight: 3,
      map,
    });
    polylines.push(polyline);
  }
}

/** Geolocate IP via backend cache (calls get_ip_loc on server). */
async function fetchIpLoc(ip: string): Promise<google.maps.LatLngLiteral | null> {
  const base = useBackendStore().apiBase.replace(/\/$/, "");
  try {
    const res = await fetch(`${base}/api/app/ip-loc/?ip=${encodeURIComponent(ip)}`, { credentials: "include" });
    if (!res.ok) return null;
    const data = await res.json();
    if (data.lat != null && data.lng != null) return { lat: data.lat, lng: data.lng };
    return null;
  } catch {
    return null;
  }
}

/* ---- Map init ---- */

function parseCenter(s: string): google.maps.LatLngLiteral {
  const [lat, lng] = String(s || "").split(",").map(Number);
  return lat && lng ? { lat, lng } : { lat: -6.2, lng: 106.8 };
}

async function loadMap() {
  if (!apiKey) {
    mapError.value = "No Google Maps API key \u2014 set NUXT_PUBLIC_GOOGLE_MAPS_API_KEY (keyless = gray tiles).";
    return;
  }
  await Promise.all([
    logoLoaded,
    new Promise<void>((resolve, reject) => {
      // ponytail: concatenation avoids SFC parser matching <script> literal
      const s = document.createElement("scr" + "ipt") as HTMLScriptElement;
      s.src = "https://maps.googleapis.com/maps/api/js?key=" + encodeURIComponent(apiKey);
      s.async = true;
      s.onload = () => resolve();
      s.onerror = () => { mapError.value = "Failed to load Google Maps script."; reject(new Error("gmaps load failed")); };
      document.head.appendChild(s);
    }),
  ]);
  const center = props.center
    || (props.lat != null && props.lng != null
      ? { lat: props.lat, lng: props.lng }
      : parseCenter(config.public.mapCenter));
  map = new google.maps.Map(mapEl.value!, {
    center,
    zoom: props.single ? props.zoom : Number(config.public.mapZoom) || 13,
  });
  if (props.single) {
    // Single-pin map: no clustering, so mount the marker directly.
    map.setOptions({ streetViewControl: false });
    addMemberMarker({ lat: props.lat!, lng: props.lng!, name: "", member_id: "", color: "#0ea5e9" })
      .setMap(map);
  } else {
    await refreshMarkers();
    if (props.routes && props.routes.length > 0) {
      await drawPolylines();
    }
  }
  ready.value = true;
}

onMounted(async () => {
  const loggedIn = await requireAuth();
  if (!loggedIn) return;
  await loadMap();
  if (props.single) return;
  const interval = Number(config.public.mapRefreshInterval || 300) * 1000;
  const t = setInterval(() => {
    refreshMarkers();
    if (props.routes && props.routes.length > 0) drawPolylines();
  }, Number.isFinite(interval) && interval > 0 ? interval : 300_000);
  onUnmounted(() => clearInterval(t));
});
</script>
