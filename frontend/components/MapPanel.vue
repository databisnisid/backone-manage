<template>
  <div class="relative h-full">
    <div
      v-if="!ready"
      class="absolute inset-x-4 top-4 z-10 rounded-lg border border-default bg-(--ui-bg) p-5 text-sm text-(--ui-text-dimmed) shadow-sm"
    >
      {{ mapError || "Loading map…" }}
    </div>
    <div
      ref="mapEl"
      class="w-full overflow-hidden rounded-lg border border-default shadow-sm"
      :class="height"
    ></div>
  </div>
</template>

<script setup lang="ts">
import type { Member } from "~/types/api";

const config = useRuntimeConfig();
const apiKey = config.public.googleMapsApiKey || "";
const mapEl = ref<HTMLElement | null>(null);
const ready = ref(false);
const mapError = ref("");

let map: google.maps.Map | null = null;
let markers: google.maps.Marker[] = [];
let flyers: google.maps.Circle[] = [];

const props = withDefaults(
  defineProps<{
    /** Optional center (single-member view) — overrides mapCenter config */
    lat?: number | null;
    lng?: number | null;
    /** Map height class; default 600px dashboard style */
    height?: string;
    /** Map zoom; default reads mapZoom config */
    zoom?: number;
    /** Single-member view — draws one marker, no polling */
    single?: boolean;
  }>(),
  { lat: null, lng: null, height: "h-[600px]", zoom: 15, single: false },
);

async function loadMap() {
  if (!apiKey) {
    mapError.value =
      "No Google Maps API key — set NUXT_PUBLIC_GOOGLE_MAPS_API_KEY (keyless = gray tiles).";
    return;
  }
  await new Promise<void>((resolve, reject) => {
    const s = document.createElement("script");
    s.src = `https://maps.googleapis.com/maps/api/js?key=${encodeURIComponent(apiKey)}`;
    s.async = true;
    s.onload = () => resolve();
    s.onerror = () => {
      mapError.value = "Failed to load Google Maps script.";
      reject(new Error("gmaps load failed"));
    };
    document.head.appendChild(s);
  });
  const center = props.lat != null && props.lng != null
    ? { lat: props.lat, lng: props.lng }
    : parseCenter(config.public.mapCenter);
  map = new google.maps.Map(mapEl.value!, {
    center,
    zoom: props.single ? props.zoom : Number(config.public.mapZoom) || 13,
  });
  if (props.single) {
    await addMemberMarker({
      lat: props.lat!,
      lng: props.lng!,
      name: "",
      member_id: "",
      color: "#0ea5e9",
    });
  } else {
    await refreshMarkers();
  }
  ready.value = true;
}

function parseCenter(s: string): google.maps.LatLngLiteral {
  const [lat, lng] = String(s || "").split(",").map(Number);
  return lat && lng ? { lat, lng } : { lat: -6.2, lng: 106.8 };
}

async function addMemberMarker(m: {
  lat: number;
  lng: number;
  name: string;
  member_id: string;
  color: string;
}) {
  const marker = new google.maps.Marker({
    position: { lat: m.lat, lng: m.lng },
    map,
    title: m.name,
    icon: m.member_id
      ? {
          // list mode — compact status dot
          path: google.maps.SymbolPath.CIRCLE,
          scale: 8,
          fillColor: m.color,
          fillOpacity: 1,
          strokeColor: "#fff",
          strokeWeight: 1,
        }
      : {
          // single mode — full pin, anchored at the location point
          url: `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(
            `<svg xmlns="http://www.w3.org/2000/svg" width="28" height="42" viewBox="0 0 28 42"><path d="M14 0C6.3 0 0 6.3 0 14c0 10.5 14 28 14 28s14-17.5 14-28C28 6.3 21.7 0 14 0z" fill="${m.color}"/><circle cx="14" cy="14" r="6" fill="#fff"/></svg>`,
          )}`,
          anchor: new google.maps.Point(14, 42),
        },
  });
  if (m.member_id) {
    marker.addListener("click", () => {
      window.location.assign(`/app/members/${encodeURIComponent(m.member_id)}`);
    });
  }
  markers.push(marker);
}

async function refreshMarkers() {
  if (!map) return;
  const members = await api<Member[]>("/api/app/members/");
  markers.forEach((m) => m.setMap(null));
  flyers.forEach((f) => f.setMap(null));
  markers = [];
  flyers = [];
  for (const m of members) {
    if (!m.lat || !m.lng) continue;
    const color = m.is_problem ? "#dc2626" : m.is_online ? "#16a34a" : "#64748b";
    await addMemberMarker({
      lat: m.lat,
      lng: m.lng,
      name: m.name,
      member_id: m.member_id,
      color,
    });
    if (m.is_new) {
      const c = new google.maps.Circle({
        map,
        center: { lat: m.lat, lng: m.lng },
        radius: 150,
        strokeColor: "#0ea5e9",
        fillColor: "#0ea5e9",
        fillOpacity: 0.15,
      });
      flyers.push(c);
    }
  }
}

onMounted(async () => {
  const loggedIn = await requireAuth();
  if (!loggedIn) return;
  await loadMap();
  if (props.single) return; // no marker polling for single-member view
  const interval = Number(config.public.mapRefreshInterval || 300) * 1000;
  const t = setInterval(
    refreshMarkers,
    Number.isFinite(interval) && interval > 0 ? interval : 300_000,
  );
  onUnmounted(() => clearInterval(t));
});
</script>