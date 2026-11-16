<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h2 class="text-lg font-semibold">Monitor Rules</h2>
      <UButton icon="i-lucide-plus" label="Create Rule" @click="openCreate" />
    </div>
    <div class="overflow-hidden rounded-lg border border-default bg-(--ui-bg) shadow-sm">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b border-default bg-(--ui-bg-elevated) text-left text-(--ui-text-dimmed)">
            <th class="px-4 py-3 font-medium">Name</th>
            <th class="px-4 py-3 font-medium">Item</th>
            <th class="px-4 py-3 font-medium">Min</th>
            <th class="px-4 py-3 font-medium">Max</th>
            <th class="px-4 py-3 font-medium">Duration</th>
            <th class="px-4 py-3 font-medium">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="r in rules"
            :key="r.id"
            class="border-b border-default last:border-0 hover:bg-(--ui-bg-elevated)"
          >
            <td class="px-4 py-3 font-medium">{{ r.name }}</td>
            <td class="px-4 py-3">{{ r.item_name }}</td>
            <td class="px-4 py-3">{{ r.threshold_min }}</td>
            <td class="px-4 py-3">{{ r.threshold_max }}</td>
            <td class="px-4 py-3">{{ r.duration }}s</td>
            <td class="px-4 py-3">
              <div class="flex gap-1">
                <UButton icon="i-lucide-pencil" variant="ghost" size="xs" @click="openEdit(r)" />
                <UButton icon="i-lucide-trash" variant="ghost" color="error" size="xs" @click="remove(r)" />
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="space-y-2">
      <h3 class="text-base font-semibold">Monitor Items</h3>
      <div class="overflow-hidden rounded-lg border border-default bg-(--ui-bg) shadow-sm">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-default bg-(--ui-bg-elevated) text-left text-(--ui-text-dimmed)">
              <th class="px-4 py-3 font-medium">Name</th>
              <th class="px-4 py-3 font-medium">Item ID</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="i in items"
              :key="i.id"
              class="border-b border-default last:border-0 hover:bg-(--ui-bg-elevated)"
            >
              <td class="px-4 py-3 font-medium">{{ i.name }}</td>
              <td class="px-4 py-3 font-mono text-xs">{{ i.item_id }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <UModal v-model:open="showModal" :title="editing ? 'Edit Rule' : 'Create Rule'">
      <template #body>
        <UForm :state="form" @submit="save">
          <UFormField label="Name" required>
            <UInput v-model="form.name" placeholder="Rule name" />
          </UFormField>
          <UFormField label="Monitor Item" required class="mt-3">
            <USelect v-model="form.item_id" :items="items.map(i => ({ label: i.name, value: i.id }))" />
          </UFormField>
          <div class="mt-3 grid grid-cols-2 gap-4">
            <UFormField label="Min Threshold">
              <UInput v-model.number="form.threshold_min" type="number" />
            </UFormField>
            <UFormField label="Max Threshold">
              <UInput v-model.number="form.threshold_max" type="number" />
            </UFormField>
          </div>
          <UFormField label="Duration (seconds)" class="mt-3">
            <UInput v-model.number="form.duration" type="number" />
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
import type { MonitorRule, MonitorItem } from "~/types/api";

const rules = ref<MonitorRule[]>([]);
const items = ref<MonitorItem[]>([]);
[rules.value, items.value] = await Promise.all([fetchMonitorRules(), fetchMonitorItems()]);

const showModal = ref(false);
const editing = ref<MonitorRule | null>(null);
const saving = ref(false);
const form = reactive({ name: "", item_id: 0, threshold_min: 0, threshold_max: 100, duration: 300 });

function openCreate() {
  editing.value = null;
  form.name = "";
  form.item_id = items.value[0]?.id ?? 0;
  form.threshold_min = 0;
  form.threshold_max = 100;
  form.duration = 300;
  showModal.value = true;
}
function openEdit(r: MonitorRule) {
  editing.value = r;
  form.name = r.name;
  form.item_id = r.item_id;
  form.threshold_min = r.threshold_min;
  form.threshold_max = r.threshold_max;
  form.duration = r.duration;
  showModal.value = true;
}
async function save() {
  saving.value = true;
  try {
    if (editing.value) {
      await updateMonitorRule(editing.value.id, { ...form });
    } else {
      await createMonitorRule({ ...form });
    }
    rules.value = await fetchMonitorRules();
    showModal.value = false;
  } catch (e: any) {
    console.error(e);
  } finally {
    saving.value = false;
  }
}
async function remove(r: MonitorRule) {
  if (!confirm(`Delete rule "${r.name}"?`)) return;
  await deleteMonitorRule(r.id);
  rules.value = rules.value.filter((x) => x.id !== r.id);
}
</script>
