<template>
  <div class="relative h-full">
    <div
      v-if="!ready"
      class="absolute inset-x-4 top-4 z-10 rounded-lg border border-default bg-(--ui-bg) p-5 text-sm text-(--ui-text-dimmed) shadow-sm"
    >
      {{ mapError || "Loading map\u2026" }}
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

async function refreshMarkers() {
  if (!map) return;
  const members = props.members && props.members.length > 0
    ? props.members
    : await api<Member[]>("/api/app/members/");
  clusterer?.clearMarkers();
  markers.forEach((m) => m.setMap(null));
  flyers.forEach((f) => f.setMap(null));
  markers = [];
  flyers = [];
  // V20: null check, not falsy — a coord of 0 is a real location.
  const located = members.filter(
    (m): m is Member & { lat: number; lng: number } => m.lat != null && m.lng != null,
  );
  const created: google.maps.Marker[] = [];
  for (const m of located) {
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
  // Fit once, like the dashboard's calculateMapCenter: with a fixed center the
  // pins land off-screen. Later refreshes keep the user's viewport.
  if (!fitted && located.length > 0) {
    fitted = true;
    if (located.length === 1) {
      map.setCenter({ lat: located[0].lat, lng: located[0].lng });
    } else {
      const bounds = new google.maps.LatLngBounds();
      located.forEach((m) => bounds.extend({ lat: m.lat, lng: m.lng }));
      map.fitBounds(bounds, 60);
      // Jitter clusters members within a few hundred metres, so a raw fit
      // zooms to street level and explodes the bubble. Cap it at the configured
      // zoom — same view the dashboard shows.
      const maxZoom = Number(config.public.mapZoom) || 13;
      const once = map.addListener("idle", () => {
        google.maps.event.removeListener(once);
        if ((map?.getZoom() ?? 0) > maxZoom) map.setZoom(maxZoom);
      });
    }
  }
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
