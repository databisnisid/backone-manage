<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h2 class="text-lg font-semibold">Web Filters</h2>
      <UButton icon="i-lucide-plus" label="Create" @click="openCreate" />
    </div>
    <div class="overflow-hidden rounded-lg border border-default bg-(--ui-bg) shadow-sm">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b border-default bg-(--ui-bg-elevated) text-left text-(--ui-text-dimmed)">
            <th class="px-4 py-3 font-medium">Name</th>
            <th class="px-4 py-3 font-medium">Default Block</th>
            <th class="px-4 py-3 font-medium">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="wf in webfilters"
            :key="wf.id"
            class="border-b border-default last:border-0 hover:bg-(--ui-bg-elevated)"
          >
            <td class="px-4 py-3 font-medium">{{ wf.name }}</td>
            <td class="px-4 py-3">{{ wf.is_default_block ? "Yes" : "No" }}</td>
            <td class="px-4 py-3">
              <div class="flex gap-1">
                <UButton icon="i-lucide-pencil" variant="ghost" size="xs" @click="openEdit(wf)" />
                <UButton icon="i-lucide-trash" variant="ghost" color="error" size="xs" @click="remove(wf)" />
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <UModal v-model:open="showModal" :title="editing ? 'Edit WebFilter' : 'Create WebFilter'">
      <template #body>
        <UForm :state="form" @submit="save">
          <UFormField label="Name" required>
            <UInput v-model="form.name" placeholder="Filter name" />
          </UFormField>
          <UFormField label="Default Block" class="mt-3">
            <UToggle v-model="form.is_default_block" />
          </UFormField>
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
import type { WebFilter } from "~/types/api";

const webfilters = ref<WebFilter[]>([]);
webfilters.value = await fetchWebfilters();

const showModal = ref(false);
const editing = ref<WebFilter | null>(null);
const saving = ref(false);
const form = reactive({ name: "", is_default_block: true });

function openCreate() {
  editing.value = null;
  form.name = "";
  form.is_default_block = true;
  showModal.value = true;
}
function openEdit(wf: WebFilter) {
  editing.value = wf;
  form.name = wf.name;
  form.is_default_block = wf.is_default_block;
  showModal.value = true;
}
async function save() {
  saving.value = true;
  try {
    if (editing.value) {
      await updateWebfilter(editing.value.id, { ...form });
    } else {
      await api<WebFilter>("/api/app/webfilters/", { method: "POST", body: JSON.stringify({ ...form }) });
    }
    webfilters.value = await fetchWebfilters();
    showModal.value = false;
  } catch (e: any) {
    console.error(e);
  } finally {
    saving.value = false;
  }
}
async function remove(wf: WebFilter) {
  if (!confirm(`Delete "${wf.name}"?`)) return;
  await deleteWebfilter(wf.id);
  webfilters.value = webfilters.value.filter((w) => w.id !== wf.id);
}
</script>
