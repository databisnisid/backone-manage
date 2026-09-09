<template>
  <UDashboardPanel id="networks">
    <template #header>
      <UDashboardNavbar title="Networks">
        <template #leading>
          <UDashboardSidebarCollapse />
        </template>
        <template #trailing>
          <UButton
            icon="i-lucide-plus"
            label="Create Network"
            @click="showCreate = true"
          />
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
              <tr
                v-for="n in networks"
                :key="n.network_id"
                class="cursor-pointer border-b border-default last:border-0 hover:bg-(--ui-bg-elevated)"
                @click="navigateTo(`/networks/${n.network_id}`)"
              >
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

      <UModal v-model:open="showCreate" title="Create Network">
        <template #body>
          <div class="space-y-4">
            <div>
              <label class="mb-1 block text-sm font-medium">Name</label>
              <UInput v-model="form.name" placeholder="e.g. Main Network" />
            </div>
            <div>
              <label class="mb-1 block text-sm font-medium">Description</label>
              <UInput v-model="form.description" placeholder="Optional description" />
            </div>
            <div>
              <label class="mb-1 block text-sm font-medium">IP Allocation (CIDR)</label>
              <UInput v-model="form.ip_allocation" placeholder="e.g. 192.168.0.0/24, 10.0.0.0/24" />
            </div>
            <div v-if="error" class="text-sm text-red-500">{{ error }}</div>
          </div>
        </template>
        <template #footer>
          <UButton label="Cancel" variant="outline" @click="showCreate = false" />
          <UButton
            label="Create"
            :loading="submitting"
            :disabled="!form.name.trim()"
            @click="handleCreate"
          />
        </template>
      </UModal>
    </template>
  </UDashboardPanel>
</template>

<script setup lang="ts">
import type { Network } from "~/types/api";
import { createNetwork } from "~/utils/api";

const networks = ref<Network[]>([]);
const auth = useAuthStore();
await requireAuth();
if (auth.loggedIn) {
  networks.value = await api<Network[]>("/api/app/networks/");
}

const showCreate = ref(false);
const submitting = ref(false);
const error = ref("");
const form = ref({ name: "", description: "", ip_allocation: "" });

async function handleCreate() {
  if (!form.value.name.trim()) return;
  submitting.value = true;
  error.value = "";
  try {
    const net = await createNetwork({
      name: form.value.name.trim(),
      description: form.value.description.trim(),
      ip_allocation: form.value.ip_allocation.trim(),
    });
    showCreate.value = false;
    form.value = { name: "", description: "", ip_allocation: "" };
    navigateTo(`/networks/${net.network_id}`);
  } catch (e: any) {
    const data = e?.response?._data;
    if (data?.error?.name) error.value = data.error.name[0];
    else if (typeof data?.error === "string") error.value = data.error;
    else error.value = "Failed to create network.";
  } finally {
    submitting.value = false;
  }
}
</script>
