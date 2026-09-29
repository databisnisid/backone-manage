<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h2 class="text-lg font-semibold">Features</h2>
      <UButton icon="i-lucide-plus" label="Create Feature" @click="openCreate" />
    </div>
    <div class="overflow-hidden rounded-lg border border-default bg-(--ui-bg) shadow-sm">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b border-default bg-(--ui-bg-elevated) text-left text-(--ui-text-dimmed)">
            <th class="px-4 py-3 font-medium">Name</th>
            <th class="px-4 py-3 font-medium">Networks</th>
            <th class="px-4 py-3 font-medium">Members</th>
            <th class="px-4 py-3 font-medium">Created</th>
            <th class="px-4 py-3 font-medium">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="f in features"
            :key="f.id"
            class="border-b border-default last:border-0 hover:bg-(--ui-bg-elevated)"
          >
            <td class="px-4 py-3 font-medium">{{ f.name }}</td>
            <td class="px-4 py-3">{{ f.number_of_network }}</td>
            <td class="px-4 py-3">{{ f.number_of_member }}</td>
            <td class="px-4 py-3">{{ formatDate(f.created_at) }}</td>
            <td class="px-4 py-3">
              <div class="flex justify-end gap-2">
                <UButton icon="i-lucide-pencil" color="neutral" variant="ghost" @click="openEdit(f)" />
                <UButton icon="i-lucide-trash" color="error" variant="ghost" @click="remove(f)" />
              </div>
            </td>
          </tr>
          <tr v-if="!features.length">
            <td colspan="5" class="px-4 py-6 text-center text-(--ui-text-dimmed)">No features</td>
          </tr>
        </tbody>
      </table>
    </div>

    <UModal v-model:open="showModal" :title="editing ? 'Edit Feature' : 'Create Feature'" size="xl">
      <template #body>
        <UForm class="space-y-3">
          <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <UFormField label="Name">
              <UInput v-model="form.name" class="w-full" />
            </UFormField>
            <UFormField label="Description">
              <UInput v-model="form.description" class="w-full" />
            </UFormField>
            <UFormField label="Number of Networks">
              <UInput v-model.number="form.number_of_network" type="number" min="0" class="w-full" />
            </UFormField>
            <UFormField label="Number of Members">
              <UInput v-model.number="form.number_of_member" type="number" min="0" class="w-full" />
            </UFormField>
          </div>
          <div class="grid grid-cols-2 gap-x-4 gap-y-2 sm:grid-cols-3">
            <label
              v-for="b in BOOL_FIELDS"
              :key="b.key"
              class="flex items-center justify-between gap-2 rounded border border-default px-3 py-1.5 text-sm"
            >
              <span>{{ b.label }}</span>
              <USwitch :model-value="!!form[b.key]" @update:model-value="(v: boolean) => (form[b.key] = v)" />
            </label>
          </div>
        </UForm>
      </template>
      <template #footer>
        <div class="flex justify-end gap-2">
          <UButton label="Cancel" color="neutral" variant="outline" @click="showModal = false" />
          <UButton label="Save" :loading="saving" @click="save" />
        </div>
      </template>
    </UModal>
  </div>
</template>

<script setup lang="ts">
import type { Feature } from "~/types/api";

const BOOL_FIELDS = [
  { key: "network_multi_ip", label: "Multi IP Network" },
  { key: "network_rules", label: "Network Rules" },
  { key: "member_multi_ip", label: "Multi IP Member" },
  { key: "authorize", label: "Authorize" },
  { key: "bridge", label: "Bridge" },
  { key: "tags", label: "Tags" },
  { key: "web", label: "Web" },
  { key: "ssh", label: "SSH" },
  { key: "synchronize", label: "Synchronize" },
  { key: "geolocation", label: "Geolocation" },
  { key: "online_offline", label: "Online/Offline" },
  { key: "is_export", label: "Export" },
  { key: "mobile_connect", label: "Mobile Connect" },
  { key: "map_dashboard", label: "Map Dashboard" },
  { key: "is_nms", label: "NMS" },
  { key: "is_webfilter", label: "Web Filter" },
  { key: "is_webfilter_multinet", label: "Web Filter Multinet" },
  { key: "is_dpi", label: "DPI" },
  { key: "is_telkomsel", label: "Telkomsel" },
  { key: "is_deauth_timer", label: "Deauth Timer" },
  { key: "is_simple_list", label: "Simple List" },
  { key: "is_lte_signal", label: "LTE Signal" },
] as const;

const features = ref<Feature[]>([]);
const auth = useAuthStore();
await requireAuth();
if (auth.loggedIn) {
  features.value = await fetchFeatures();
}

const showModal = ref(false);
const saving = ref(false);
const editing = ref<Feature | null>(null);
const form = reactive<Partial<Feature>>({});

function blankForm(): Partial<Feature> {
  const f: Record<string, unknown> = {
    name: "",
    description: "",
    number_of_network: 1,
    number_of_member: 1,
  };
  for (const b of BOOL_FIELDS) f[b.key] = false;
  return f as Partial<Feature>;
}

function openCreate() {
  editing.value = null;
  Object.assign(form, blankForm());
  showModal.value = true;
}

function openEdit(f: Feature) {
  editing.value = f;
  Object.assign(form, blankForm(), f);
  showModal.value = true;
}

async function save() {
  saving.value = true;
  try {
    const body: Partial<Feature> = {
      name: form.name,
      description: form.description,
      number_of_network: form.number_of_network,
      number_of_member: form.number_of_member,
    };
    for (const b of BOOL_FIELDS) body[b.key] = form[b.key];
    if (editing.value) {
      const updated = await updateFeature(editing.value.id, body);
      features.value = features.value.map((x) => (x.id === updated.id ? updated : x));
    } else {
      features.value.push(await createFeature(body));
    }
    showModal.value = false;
  } catch (e: any) {
    console.error(e);
    alert(e?.message || "Save failed");
  } finally {
    saving.value = false;
  }
}

async function remove(f: Feature) {
  if (!confirm(`Delete feature "${f.name}"?`)) return;
  await deleteFeature(f.id);
  features.value = features.value.filter((x) => x.id !== f.id);
}

function formatDate(s: string | null) {
  return s ? new Date(s).toLocaleDateString() : "—";
}
</script>
