<template>
  <UDashboardPanel id="home">
    <template #header>
      <UDashboardNavbar title="Dashboard">
        <template #leading>
          <UDashboardSidebarCollapse />
        </template>
      </UDashboardNavbar>
    </template>

    <template #body>
      <div v-if="summary" class="grid grid-cols-2 gap-4 px-4 py-4 md:grid-cols-4">
        <div
          v-for="card in cards"
          :key="card.label"
          class="rounded-lg border border-default bg-(--ui-bg) p-5 shadow-sm"
        >
          <div class="text-sm text-(--ui-text-dimmed)">{{ card.label }}</div>
          <div :class="['mt-1 text-3xl font-semibold', card.color]">{{ card.value }}</div>
        </div>
      </div>
      <div v-else class="px-4 py-4 text-sm text-(--ui-text-dimmed)">Loading…</div>

      <div class="px-4 pb-4">
        <div class="mb-2 flex items-center justify-between">
          <h2 class="text-lg font-semibold">Map</h2>
          <span class="text-xs text-(--ui-text-dimmed)">Auto-refresh {{ Math.round((Number(config.public.mapRefreshInterval || 300)) / 60) }} min</span>
        </div>
        <MapPanel />
      </div>
    </template>
  </UDashboardPanel>
</template>

<script setup lang="ts">
import type { Summary } from "~/types/api";

const summary = ref<Summary | null>(null);
const auth = useAuthStore();
const loggedIn = await requireAuth();
if (loggedIn) {
  summary.value = await api<Summary>("/api/app/summary/");
}
const config = useRuntimeConfig();
const cards = computed(() => [
  { label: "Members", value: summary.value?.members ?? 0, color: "text-(--ui-text)" },
  { label: "Online", value: summary.value?.online ?? 0, color: "text-emerald-600" },
  { label: "Problems", value: summary.value?.problems ?? 0, color: "text-red-600" },
  { label: "Networks", value: summary.value?.networks ?? 0, color: "text-sky-600" },
]);
const refresh = async () => {
  if (auth.loggedIn) summary.value = await api<Summary>("/api/app/summary/");
};
const interval = Number(config.public.mapRefreshInterval || 300) * 1000;
const t = setInterval(refresh, Number.isFinite(interval) && interval > 0 ? interval : 300_000);
onUnmounted(() => clearInterval(t));
</script>