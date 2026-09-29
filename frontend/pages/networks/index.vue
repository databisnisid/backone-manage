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
            @click="openCreate"
          />
        </template>
      </UDashboardNavbar>
    </template>

    <template #body>
      <div class="space-y-4 p-4">
        <UInput
          v-model="search"
          icon="i-lucide-search"
          placeholder="Search by name or network ID…"
          class="max-w-sm"
        />
        <p class="text-xs text-(--ui-text-dimmed)">Showing {{ networks.length }} networks</p>
        <div class="overflow-hidden rounded-lg border border-default bg-(--ui-bg) shadow-sm">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-default bg-(--ui-bg-elevated) text-left text-(--ui-text-dimmed)">
                <th class="px-4 py-3 font-medium">Name</th>
                <th class="px-4 py-3 font-medium">Network ID</th>
                <th class="px-4 py-3 font-medium">Description</th>
                <th class="px-4 py-3 font-medium">CIDR</th>
                <th class="px-4 py-3 font-medium">Members</th>
                <th class="px-4 py-3 font-medium">Routes</th>
                <th class="px-4 py-3 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="n in filteredNetworks"
                :key="n.network_id"
                class="border-b border-default last:border-0 hover:bg-(--ui-bg-elevated)"
              >
                <td class="px-4 py-3 font-medium">{{ n.name }}</td>
                <td class="px-4 py-3 font-mono text-xs text-(--ui-text-dimmed)">{{ n.network_id }}</td>
                <td class="px-4 py-3 text-(--ui-text-dimmed)">{{ n.description || "—" }}</td>
                <td class="px-4 py-3 font-mono text-xs text-(--ui-text-dimmed)">{{ n.ip_allocation || "—" }}</td>
                <td class="px-4 py-3">{{ n.member_count }}</td>
                <td class="px-4 py-3">{{ n.route_count }}</td>
                <td class="px-4 py-3 flex gap-1">
                  <UButton
                    v-if="auth.isSuperuser"
                    icon="i-lucide-route"
                    variant="ghost"
                    size="xs"
                    label="Routes"
                    @click="navigateTo(`/networks/${n.network_id}`)"
                  />
                  <UButton
                    icon="i-lucide-pencil"
                    variant="ghost"
                    size="xs"
                    @click="openEdit(n)"
                  />
                </td>
              </tr>
            </tbody>
          </table>
          <div v-if="filteredNetworks.length === 0" class="p-6 text-sm text-(--ui-text-dimmed)">No networks.</div>
        </div>
      </div>

      <UModal v-model:open="modalOpen" :title="editing ? 'Edit Network' : 'Create Network'">
        <template #body>
          <UForm :state="form" @submit="submit">
            <UFormField label="Name" name="name" required>
              <UInput v-model="form.name" placeholder="Network name" />
            </UFormField>
            <UFormField label="Description" name="description">
              <UInput v-model="form.description" placeholder="Optional description" />
            </UFormField>
            <UFormField label="IP Allocation (CIDR)" name="ip_allocation">
              <UInput v-model="form.ip_allocation" placeholder="e.g. 10.0.0.0/24" />
            </UFormField>
            <div class="flex justify-end gap-2 pt-4">
              <UButton variant="outline" @click="modalOpen = false">Cancel</UButton>
              <UButton type="submit" :loading="saving">
                {{ editing ? "Update" : "Create" }}
              </UButton>
            </div>
          </UForm>
        </template>
      </UModal>
    </template>
  </UDashboardPanel>
</template>

<script setup lang="ts">
import type { Network, NetworkDetail } from "~/types/api";

const networks = ref<Network[]>([]);
const search = ref("");
const auth = useAuthStore();
await requireAuth();
if (auth.loggedIn) {
  networks.value = await api<Network[]>("/api/app/networks/");
}

const filteredNetworks = computed(() => {
  const q = search.value.trim().toLowerCase();
  if (!q) return networks.value;
  return networks.value.filter(
    (n) =>
      n.name.toLowerCase().includes(q) ||
      n.network_id.toLowerCase().includes(q),
  );
});

// Modal state
const modalOpen = ref(false);
const editing = ref<NetworkDetail | null>(null);
const saving = ref(false);
const form = reactive({ name: "", description: "", ip_allocation: "" });

function openCreate() {
  editing.value = null;
  form.name = "";
  form.description = "";
  form.ip_allocation = "";
  modalOpen.value = true;
}

function openEdit(n: Network) {
  editing.value = n as unknown as NetworkDetail;
  form.name = n.name;
  form.description = n.description || "";
  form.ip_allocation = n.ip_allocation || "";
  modalOpen.value = true;
}

async function submit() {
  saving.value = true;
  try {
    if (editing.value) {
      await updateNetwork(editing.value.network_id, {
        name: form.name,
        description: form.description,
        ip_allocation: form.ip_allocation,
      });
    } else {
      await createNetwork({
        name: form.name,
        description: form.description,
        ip_allocation: form.ip_allocation,
      });
    }
    modalOpen.value = false;
    networks.value = await api<Network[]>("/api/app/networks/");
  } finally {
    saving.value = false;
  }
}
</script>
