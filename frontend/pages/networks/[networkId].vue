<template>
  <UDashboardPanel id="network-detail">
    <template #header>
      <UDashboardNavbar :title="network?.name || 'Network'">
        <template #leading>
          <UButton icon="i-lucide-arrow-left" variant="ghost" @click="navigateTo('/networks')" />
        </template>
        <template #trailing>
          <UButton icon="i-lucide-edit" label="Edit" variant="outline" @click="openNetworkEdit" />
        </template>
      </UDashboardNavbar>
    </template>

    <template #body>
      <div v-if="loading" class="p-6 text-sm text-(--ui-text-dimmed)">Loading...</div>

      <div v-else-if="network" class="space-y-6 p-4">
        <!-- Network Info Card -->
        <div class="rounded-lg border border-default bg-(--ui-bg) p-4 shadow-sm">
          <h3 class="mb-2 text-sm font-semibold text-(--ui-text-highlighted)">Network Info</h3>
          <div class="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span class="text-(--ui-text-dimmed)">Name:</span>
              <span class="ml-2 font-medium">{{ network.name }}</span>
            </div>
            <div>
              <span class="text-(--ui-text-dimmed)">Network ID:</span>
              <span class="ml-2 font-mono text-xs">{{ network.network_id }}</span>
            </div>
            <div>
              <span class="text-(--ui-text-dimmed)">Members:</span>
              <span class="ml-2 font-medium">{{ network.member_count }}</span>
            </div>
            <div v-if="network.description">
              <span class="text-(--ui-text-dimmed)">Description:</span>
              <span class="ml-2">{{ network.description }}</span>
            </div>
          </div>
        </div>

        <!-- Routes Table -->
        <div class="rounded-lg border border-default bg-(--ui-bg) shadow-sm">
          <div class="flex items-center justify-between border-b border-default px-4 py-3">
            <h3 class="text-sm font-semibold text-(--ui-text-highlighted)">
              Routes ({{ routes.length }})
            </h3>
            <UButton
              icon="i-lucide-plus"
              label="Add Route"
              size="xs"
              @click="showCreateModal = true"
            />
          </div>

          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-default bg-(--ui-bg-elevated) text-left text-(--ui-text-dimmed)">
                <th class="px-4 py-3 font-medium">Target (CIDR)</th>
                <th class="px-4 py-3 font-medium">Gateway</th>
                <th class="px-4 py-3 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="r in routes"
                :key="r.id"
                class="border-b border-default last:border-0"
              >
                <td class="px-4 py-3 font-mono text-xs">{{ r.ip_network }}</td>
                <td class="px-4 py-3 font-mono text-xs">{{ r.gateway || '—' }}</td>
                <td class="px-4 py-3 text-right">
                  <div class="flex items-center justify-end gap-1">
                    <UButton
                      icon="i-lucide-pencil"
                      size="xs"
                      variant="ghost"
                      @click="openEditModal(r)"
                    />
                    <UButton
                      icon="i-lucide-trash-2"
                      size="xs"
                      variant="ghost"
                      color="error"
                      @click="confirmDelete(r)"
                    />
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
          <div v-if="routes.length === 0" class="p-6 text-center text-sm text-(--ui-text-dimmed)">
            No routes configured.
          </div>
        </div>

        <!-- Map with polylines -->
        <div class="h-[400px] rounded-lg border border-default bg-(--ui-bg) shadow-sm lg:h-[500px]">
          <MapPanel
            :members="mapMembers"
            :routes="routes"
            :center="mapCenter"
          />
        </div>
      </div>

      <!-- Create Route Modal -->
      <UModal v-model:open="showCreateModal" title="Add Route">
        <template #body>
          <div class="space-y-4">
            <UFormField label="Target (CIDR)" required>
              <UInput
                v-model="createForm.ip_network"
                placeholder="192.168.0.0/24"
              />
            </UFormField>
            <UFormField label="Gateway (optional)">
              <UInput
                v-model="createForm.gateway"
                placeholder="10.0.0.1"
              />
            </UFormField>
          </div>
        </template>
        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton label="Cancel" variant="ghost" @click="showCreateModal = false" />
            <UButton
              label="Create"
              :loading="submitting"
              @click="submitCreate"
            />
          </div>
        </template>
      </UModal>

      <!-- Edit Route Modal -->
      <UModal v-model:open="showEditModal" title="Edit Route">
        <template #body>
          <div class="space-y-4">
            <UFormField label="Target (CIDR)">
              <UInput
                v-model="editForm.ip_network"
                :disabled="true"
              />
            </UFormField>
            <UFormField label="Gateway (optional)">
              <UInput
                v-model="editForm.gateway"
                placeholder="10.0.0.1"
              />
            </UFormField>
          </div>
        </template>
        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton label="Cancel" variant="ghost" @click="showEditModal = false" />
            <UButton
              label="Save"
              :loading="submitting"
              @click="submitEdit"
            />
          </div>
        </template>
      </UModal>

      <!-- Delete Confirmation Modal -->
      <UModal v-model:open="showDeleteModal" title="Delete Route">
        <template #body>
          <p class="text-sm">
            Are you sure you want to delete route
            <span class="font-mono font-medium">{{ deletingRoute?.ip_network }}</span>?
          </p>
        </template>
        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton label="Cancel" variant="ghost" @click="showDeleteModal = false" />
            <UButton
              label="Delete"
              color="error"
              :loading="submitting"
              @click="submitDelete"
            />
          </div>
        </template>
      </UModal>

      <!-- Edit Network Modal -->
      <UModal v-model:open="showNetworkEdit" title="Edit Network">
        <template #body>
          <div class="space-y-4">
            <div>
              <label class="mb-1 block text-sm font-medium">Name</label>
              <UInput v-model="networkEditForm.name" />
            </div>
            <div>
              <label class="mb-1 block text-sm font-medium">Description</label>
              <UInput v-model="networkEditForm.description" />
            </div>
            <div>
              <label class="mb-1 block text-sm font-medium">IP Allocation (CIDR)</label>
              <UInput v-model="networkEditForm.ip_allocation" placeholder="e.g. 192.168.0.0/24" />
            </div>
            <div v-if="networkError" class="text-sm text-red-500">{{ networkError }}</div>
          </div>
        </template>
        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton label="Cancel" variant="outline" @click="showNetworkEdit = false" />
            <UButton label="Save" :loading="submitting" :disabled="!networkEditForm.name.trim()" @click="submitNetworkEdit" />
          </div>
        </template>
      </UModal>
    </template>
  </UDashboardPanel>
</template>

<script setup lang="ts">
import type { Network, Route } from "~/types/api";
import { fetchRoutes, createRoute, updateRoute, deleteRoute, fetchNetworkDetail, updateNetwork } from "~/utils/api";

const route = useRoute();
const networkId = route.params.networkId as string;

const network = ref<Network | null>(null);
const routes = ref<Route[]>([]);
const loading = ref(true);
const submitting = ref(false);

// Modals
const showCreateModal = ref(false);
const showEditModal = ref(false);
const showDeleteModal = ref(false);
const deletingRoute = ref<Route | null>(null);

// Forms
const createForm = reactive({ ip_network: "", gateway: "" });
const editForm = reactive({ ip_network: "", gateway: "" });

// Network edit
const showNetworkEdit = ref(false);
const networkEditForm = reactive({ name: "", description: "", ip_allocation: "" });
const networkError = ref("");

// Map center (fallback to Monas)
const mapCenter = ref({ lat: -6.1754, lng: 106.8271 });
const mapMembers = ref<any[]>([]);

// Auth
const auth = useAuthStore();
await requireAuth();
if (!auth.loggedIn) {
  throw createError({ statusCode: 401, statusMessage: "Unauthorized" });
}

// Load data
async function loadData() {
  loading.value = true;
  try {
    const [netDetail, routeList] = await Promise.all([
      fetchNetworkDetail(networkId),
      fetchRoutes(networkId),
    ]);
    network.value = netDetail as any;
    routes.value = routeList;
  } catch (e) {
    console.error("Failed to load network data:", e);
  } finally {
    loading.value = false;
  }
}

await loadData();

// Route Create
async function submitCreate() {
  if (!createForm.ip_network.trim()) return;
  submitting.value = true;
  try {
    const newRoute = await createRoute(networkId, createForm.ip_network.trim(), createForm.gateway.trim() || null);
    routes.value.push(newRoute);
    showCreateModal.value = false;
    createForm.ip_network = "";
    createForm.gateway = "";
  } catch (e: any) {
    console.error("Create failed:", e);
  } finally {
    submitting.value = false;
  }
}

// Route Edit
function openEditModal(r: Route) {
  editForm.ip_network = r.ip_network;
  editForm.gateway = r.gateway || "";
  showEditModal.value = true;
}

async function submitEdit() {
  submitting.value = true;
  try {
    const updated = await updateRoute(networkId, editForm.ip_network, {
      gateway: editForm.gateway.trim() || null,
    });
    const idx = routes.value.findIndex((r) => r.ip_network === editForm.ip_network);
    if (idx !== -1) routes.value[idx] = updated;
    showEditModal.value = false;
  } catch (e: any) {
    console.error("Update failed:", e);
  } finally {
    submitting.value = false;
  }
}

// Route Delete
function confirmDelete(r: Route) {
  deletingRoute.value = r;
  showDeleteModal.value = true;
}

async function submitDelete() {
  if (!deletingRoute.value) return;
  submitting.value = true;
  try {
    await deleteRoute(networkId, deletingRoute.value.ip_network);
    routes.value = routes.value.filter((r) => r.id !== deletingRoute.value!.id);
    showDeleteModal.value = false;
    deletingRoute.value = null;
  } catch (e: any) {
    console.error("Delete failed:", e);
  } finally {
    submitting.value = false;
  }
}

// Network Edit
function openNetworkEdit() {
  if (network.value) {
    networkEditForm.name = network.value.name;
    networkEditForm.description = (network.value as any).description || "";
    networkEditForm.ip_allocation = (network.value as any).ip_allocation || "";
    networkError.value = "";
    showNetworkEdit.value = true;
  }
}

async function submitNetworkEdit() {
  if (!networkEditForm.name.trim()) return;
  submitting.value = true;
  networkError.value = "";
  try {
    const updated = await updateNetwork(networkId, {
      name: networkEditForm.name.trim(),
      description: networkEditForm.description.trim(),
      ip_allocation: networkEditForm.ip_allocation.trim(),
    });
    network.value = { ...network.value!, name: updated.name } as Network;
    showNetworkEdit.value = false;
  } catch (e: any) {
    const data = e?.response?._data;
    if (data?.error?.name) networkError.value = data.error.name[0];
    else if (typeof data?.error === "string") networkError.value = data.error;
    else networkError.value = "Failed to update network.";
  } finally {
    submitting.value = false;
  }
}
</script>
