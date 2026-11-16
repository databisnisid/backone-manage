<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h2 class="text-lg font-semibold">Access History</h2>
      <UInput v-model="filter" icon="i-lucide-search" placeholder="Filter username / IP" class="w-64" />
    </div>

    <div class="flex gap-2">
      <UButton
        v-for="t in tabs"
        :key="t.value"
        :color="tab === t.value ? 'primary' : 'neutral'"
        :variant="tab === t.value ? 'solid' : 'outline'"
        @click="tab = t.value"
      >
        {{ t.label }}
      </UButton>
    </div>

    <div class="overflow-hidden rounded-lg border border-default bg-(--ui-bg) shadow-sm">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b border-default bg-(--ui-bg-elevated) text-left text-(--ui-text-dimmed)">
            <th class="px-4 py-3 font-medium">Username</th>
            <th class="px-4 py-3 font-medium">IP Address</th>
            <th class="px-4 py-3 font-medium">User Agent</th>
            <th class="px-4 py-3 font-medium">Attempt</th>
            <th class="px-4 py-3 font-medium">{{ tab === "logs" ? "Logout" : "Locked Out" }}</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="row in visible"
            :key="row.id"
            class="border-b border-default last:border-0 hover:bg-(--ui-bg-elevated)"
          >
            <td class="px-4 py-3 font-medium">{{ row.username || "—" }}</td>
            <td class="px-4 py-3 font-mono text-xs">{{ row.ip_address || "—" }}</td>
            <td class="max-w-xs truncate px-4 py-3 text-xs text-(--ui-text-dimmed)" :title="row.user_agent || ''">
              {{ row.user_agent || "—" }}
            </td>
            <td class="px-4 py-3 text-xs text-(--ui-text-dimmed)">{{ fmt(row.attempt_time) }}</td>
            <td class="px-4 py-3 text-xs">
              <template v-if="tab === 'logs'">{{ fmt((row as AccessLogItem).logout_time) }}</template>
              <UBadge v-else :color="(row as AccessFailureItem).locked_out ? 'error' : 'neutral'" variant="subtle">
                {{ (row as AccessFailureItem).locked_out ? "Yes" : "No" }}
              </UBadge>
            </td>
          </tr>
          <tr v-if="!visible.length">
            <td colspan="5" class="px-4 py-6 text-center text-(--ui-text-dimmed)">No records</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { AccessFailureItem, AccessLogItem } from "~/types/api";

const tab = ref<"logs" | "failures">("logs");
const filter = ref("");

const tabs = [
  { label: "Logins", value: "logs" as const },
  { label: "Failures", value: "failures" as const },
];

const data = await fetchAccessLogs();

const visible = computed(() => {
  const q = filter.value.trim().toLowerCase();
  const rows = tab.value === "logs" ? data.logs : data.failures;
  if (!q) return rows;
  return rows.filter(
    (r) => r.username?.toLowerCase().includes(q) || r.ip_address?.toLowerCase().includes(q),
  );
});

function fmt(value: string | null | undefined) {
  return value ? new Date(value).toLocaleString() : "—";
}
</script>
