<template>
  <UDashboardPanel id="networks">
    <template #header>
      <UDashboardNavbar title="Networks">
        <template #leading>
          <UDashboardSidebarCollapse />
        </template>
      </UDashboardNavbar>
    </template>

    <template #body>
      <div class="p-4">
        <div class="overflow-hidden rounded-lg border border-default bg-(--ui-bg) shadow-sm">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-default bg-(--ui-bg-elevated) text-left text-(--ui-text-dimmed)">
                <th class="px-4 py-3 font-medium">Name</th>
                <th class="px-4 py-3 font-medium">Network ID</th>
                <th class="px-4 py-3 font-medium">Members</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="n in networks" :key="n.network_id" class="border-b border-default last:border-0">
                <td class="px-4 py-3 font-medium">{{ n.name }}</td>
                <td class="px-4 py-3 font-mono text-xs text-(--ui-text-dimmed)">{{ n.network_id }}</td>
                <td class="px-4 py-3">
                  <UBadge color="info" variant="subtle" size="sm">
                    <template #leading>
                      <span class="size-1.5 rounded-full bg-sky-500" />
                    </template>
                    {{ n.member_count }} member{{ n.member_count === 1 ? "" : "s" }}
                  </UBadge>
                </td>
              </tr>
            </tbody>
          </table>
          <div v-if="networks.length === 0" class="p-6 text-sm text-(--ui-text-dimmed)">No networks.</div>
        </div>
      </div>
    </template>
  </UDashboardPanel>
</template>

<script setup lang="ts">
import type { Network } from "~/types/api";

const networks = ref<Network[]>([]);
const auth = useAuthStore();
await requireAuth();
if (auth.loggedIn) {
  networks.value = await api<Network[]>("/api/app/networks/");
}
</script>