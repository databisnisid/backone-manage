<template>
  <UDashboardPanel id="network-detail">
    <template #header>
      <UDashboardNavbar :title="net?.name || 'Network'">
        <template #leading>
          <UDashboardSidebarCollapse />
        </template>
        <template #trailing>
          <UButton
            icon="i-lucide-arrow-left"
            label="Back to Networks"
            variant="ghost"
            @click="navigateTo('/networks')"
          />
        </template>
      </UDashboardNavbar>
    </template>

    <template #body>
      <div class="space-y-4 p-4">
        <!-- Network info -->
        <div v-if="net" class="rounded-lg border border-default bg-(--ui-bg) p-4">
          <div class="grid grid-cols-2 gap-4 text-sm">
            <div><span class="text-(--ui-text-dimmed)">Network ID:</span> <span class="font-mono">{{ net.network_id }}</span></div>
            <div><span class="text-(--ui-text-dimmed)">Description:</span> {{ net.description || "—" }}</div>
            <div><span class="text-(--ui-text-dimmed)">CIDR:</span> <span class="font-mono">{{ net.ip_allocation || "—" }}</span></div>
            <div><span class="text-(--ui-text-dimmed)">Members:</span> {{ net.member_count }}</div>
          </div>
        </div>

        <!-- Routes -->
        <div class="flex items-center justify-between">
          <h2 class="text-sm font-medium text-(--ui-text-dimmed)">Routes</h2>
          <UButton icon="i-lucide-plus" label="Add Route" @click="openCreate" />
        </div>
        <p class="text-xs text-(--ui-text-dimmed)">Showing {{ routes.length }} routes</p>

        <div class="overflow-hidden rounded-lg border border-default bg-(--ui-bg) shadow-sm">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-default bg-(--ui-bg-elevated) text-left text-(--ui-text-dimmed)">
                <th class="px-4 py-3 font-medium">Target (CIDR)</th>
                <th class="px-4 py-3 font-medium">Gateway (via)</th>
                <th class="px-4 py-3 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="r in routes"
                :key="r.id"
                class="border-b border-default last:border-0 hover:bg-(--ui-bg-elevated)"
              >
                <td class="px-4 py-3 font-mono text-xs">{{ r.ip_network }}</td>
                <td class="px-4 py-3 font-mono text-xs text-(--ui-text-dimmed)">{{ r.gateway ? (r.gateway_member_name !== r.gateway ? `${r.gateway} (${r.gateway_member_name})` : r.gateway) : "—" }}</td>
                <td class="px-4 py-3">
                  <UButton icon="i-lucide-trash-2" variant="ghost" color="error" size="xs" @click="remove(r)" />
                </td>
              </tr>
            </tbody>
          </table>
          <div v-if="routes.length === 0" class="p-6 text-sm text-(--ui-text-dimmed)">No routes configured.</div>
        </div>
      </div>

      <UModal v-model:open="modalOpen" title="Add Route">
        <template #body>
          <UForm :state="form" @submit="submit">
            <UFormField label="Target (CIDR)" name="ip_network" required>
              <UInput v-model="form.ip_network" placeholder="e.g. 192.168.0.0/24" />
            </UFormField>
            <UFormField label="Gateway (via)" name="gateway">
              <UInput v-model="form.gateway" placeholder="e.g. 10.0.0.1 (optional)" />
            </UFormField>
            <div v-if="error" class="mt-2 p-2 rounded bg-red-50 text-red-700 text-sm dark:bg-red-900/20 dark:text-red-400">{{ error }}</div>
            <div class="flex justify-end gap-2 pt-4">
              <UButton variant="outline" @click="modalOpen = false">Cancel</UButton>
              <UButton type="submit" :loading="saving">Create</UButton>
            </div>
          </UForm>
        </template>
      </UModal>
    </template>
  </UDashboardPanel>
</template>

<script setup lang="ts">
import type { NetworkDetail, Route } from "~/types/api";
import { ApiError } from "~/utils/api";

const route = useRoute();
const networkId = route.params.network_id as string;

const loggedIn = await requireAuth();
if (!loggedIn) {
  window.location.assign("/");
}

const net = ref<NetworkDetail | null>(null);
const routes = ref<Route[]>([]);

if (loggedIn) {
  net.value = await fetchNetworkDetail(networkId);
  routes.value = await fetchRoutes(networkId);
}

// Modal state
const modalOpen = ref(false);
const saving = ref(false);
const error = ref("");
const form = reactive({ ip_network: "", gateway: "" });

function openCreate() {
  form.ip_network = "";
  form.gateway = "";
  error.value = "";
  modalOpen.value = true;
}

async function submit() {
  saving.value = true;
  error.value = "";
  try {
    await createRoute(networkId, form.ip_network, form.gateway || null);
    modalOpen.value = false;
    routes.value = await fetchRoutes(networkId);
  } catch (e: unknown) {
    const data = e instanceof ApiError ? e.data : e;
    if (typeof data === "object" && data !== null && "error" in data) {
      const errs = (data as { error: unknown }).error;
      if (typeof errs === "string") {
        error.value = errs;
      } else if (typeof errs === "object" && errs !== null) {
        error.value = Object.entries(errs as Record<string, unknown>)
          .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(", ") : String(v)}`)
          .join("; ");
      } else {
        error.value = "Save failed";
      }
    } else {
      error.value = typeof data === "string" ? data : "Save failed";
    }
  } finally {
    saving.value = false;
  }
}

async function remove(r: Route) {
  if (!confirm(`Delete route "${r.ip_network}"?`)) return;
  await deleteRoute(networkId, r.ip_network);
  routes.value = routes.value.filter((x) => x.id !== r.id);
}
</script>
