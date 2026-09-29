<template>
  <div class="space-y-4">
    <h2 class="text-lg font-semibold">Organizations &amp; Devices</h2>
    <div
      v-for="org in orgs"
      :key="org.id"
      class="overflow-hidden rounded-lg border border-default bg-(--ui-bg) shadow-sm"
    >
      <div class="flex items-center justify-between border-b border-default bg-(--ui-bg-elevated) px-4 py-3">
        <div>
          <span class="font-medium">{{ org.name }}</span>
          <span class="ml-2 text-xs text-(--ui-text-dimmed)">{{ org.uuid }}</span>
        </div>
        <span class="text-sm text-(--ui-text-dimmed)">{{ org.devices.length }} device(s)</span>
      </div>
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b border-default text-left text-(--ui-text-dimmed)">
            <th class="px-4 py-2 font-medium">Name</th>
            <th class="px-4 py-2 font-medium">Device ID</th>
            <th class="px-4 py-2 font-medium">User</th>
            <th class="px-4 py-2 font-medium">Created</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="d in org.devices"
            :key="d.id"
            class="border-b border-default last:border-0 hover:bg-(--ui-bg-elevated)"
          >
            <td class="px-4 py-2 font-medium">{{ d.name }}</td>
            <td class="px-4 py-2 font-mono text-xs">{{ d.device_id }}</td>
            <td class="px-4 py-2">{{ d.username || "—" }}</td>
            <td class="px-4 py-2">{{ formatDate(d.created_at) }}</td>
          </tr>
          <tr v-if="!org.devices.length">
            <td colspan="4" class="px-4 py-4 text-center text-(--ui-text-dimmed)">No devices</td>
          </tr>
        </tbody>
      </table>
    </div>
    <p v-if="!orgs.length" class="text-sm text-(--ui-text-dimmed)">No organizations</p>
  </div>
</template>

<script setup lang="ts">
import type { OrgWithDevices } from "~/types/api";

const orgs = ref<OrgWithDevices[]>([]);
const auth = useAuthStore();
await requireAuth();
if (auth.loggedIn) {
  orgs.value = await fetchOrganizationsDevices();
}

function formatDate(s: string | null) {
  return s ? new Date(s).toLocaleDateString() : "—";
}
</script>
