<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h2 class="text-lg font-semibold">Operational Time</h2>
      <UButton icon="i-lucide-plus" label="Create" @click="openCreate" />
    </div>
    <div class="overflow-hidden rounded-lg border border-default bg-(--ui-bg) shadow-sm">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b border-default bg-(--ui-bg-elevated) text-left text-(--ui-text-dimmed)">
            <th class="px-4 py-3 font-medium">Network</th>
            <th class="px-4 py-3 font-medium">Days</th>
            <th class="px-4 py-3 font-medium">Hours</th>
            <th class="px-4 py-3 font-medium">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="ot in operationalTimes"
            :key="ot.id"
            class="border-b border-default last:border-0 hover:bg-(--ui-bg-elevated)"
          >
            <td class="px-4 py-3 font-medium">{{ ot.network_name || ot.network_id }}</td>
            <td class="px-4 py-3">{{ enabledDays(ot) }}</td>
            <td class="px-4 py-3">{{ daySummary(ot) }}</td>
            <td class="px-4 py-3">
              <div class="flex justify-end gap-2">
                <UButton icon="i-lucide-pencil" color="neutral" variant="ghost" @click="openEdit(ot)" />
                <UButton icon="i-lucide-trash" color="error" variant="ghost" @click="remove(ot)" />
              </div>
            </td>
          </tr>
          <tr v-if="!operationalTimes.length">
            <td colspan="4" class="px-4 py-6 text-center text-(--ui-text-dimmed)">No operational times</td>
          </tr>
        </tbody>
      </table>
    </div>

    <UModal v-model:open="showModal" :title="editing ? 'Edit Operational Time' : 'Create Operational Time'">
      <template #body>
        <UForm class="space-y-3">
          <UFormField label="Network">
            <USelect
              v-model="form.network_id"
              :items="networks.map((n) => ({ label: n.name, value: n.network_id }))"
              class="w-full"
            />
          </UFormField>
          <div v-for="d in DAYS" :key="d.key" class="flex items-center gap-3">
            <USwitch v-model="form[d.flag as keyof typeof form]" />
            <span class="w-10 text-sm">{{ d.label }}</span>
            <UInput
              v-model.number="form[d.start as keyof typeof form]"
              type="number"
              min="1"
              max="24"
              class="w-20"
            />
            <span class="text-sm text-(--ui-text-dimmed)">to</span>
            <UInput
              v-model.number="form[d.end as keyof typeof form]"
              type="number"
              min="1"
              max="24"
              class="w-20"
            />
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
import type { Network, OperationalTime } from "~/types/api";

const DAYS = [
  { key: "mon", label: "Mon", flag: "is_mon", start: "mon_start", end: "mon_end" },
  { key: "tue", label: "Tue", flag: "is_tue", start: "tue_start", end: "tue_end" },
  { key: "wed", label: "Wed", flag: "is_wed", start: "wed_start", end: "wed_end" },
  { key: "thu", label: "Thu", flag: "is_thu", start: "thu_start", end: "thu_end" },
  { key: "fri", label: "Fri", flag: "is_fri", start: "fri_start", end: "fri_end" },
  { key: "sat", label: "Sat", flag: "is_sat", start: "sat_start", end: "sat_end" },
  { key: "sun", label: "Sun", flag: "is_sun", start: "sun_start", end: "sun_end" },
] as const;

const operationalTimes = ref<OperationalTime[]>([]);
const networks = ref<Network[]>([]);
const auth = useAuthStore();
await requireAuth();
if (auth.loggedIn) {
  [operationalTimes.value, networks.value] = await Promise.all([
    fetchOperationalTimes(),
    api<Network[]>("/api/app/networks/"),
  ]);
}

const showModal = ref(false);
const saving = ref(false);
const editing = ref<OperationalTime | null>(null);
const form = reactive<Partial<OperationalTime>>({});

function blankForm(): Partial<OperationalTime> {
  const f: Record<string, unknown> = { network_id: "" };
  for (const d of DAYS) {
    f[d.flag] = false;
    f[d.start] = 9;
    f[d.end] = 17;
  }
  return f as Partial<OperationalTime>;
}

function openCreate() {
  editing.value = null;
  Object.assign(form, blankForm());
  showModal.value = true;
}

function openEdit(ot: OperationalTime) {
  editing.value = ot;
  Object.assign(form, blankForm(), ot);
  showModal.value = true;
}

async function save() {
  saving.value = true;
  try {
    if (editing.value) {
      const updated = await updateOperationalTime(editing.value.id, { ...form });
      operationalTimes.value = operationalTimes.value.map((x) => (x.id === updated.id ? updated : x));
    } else {
      operationalTimes.value.push(await createOperationalTime({ ...form }));
    }
    showModal.value = false;
  } catch (e: any) {
    console.error(e);
    alert(e?.message || "Save failed");
  } finally {
    saving.value = false;
  }
}

async function remove(ot: OperationalTime) {
  if (!confirm(`Delete operational time for "${ot.network_name || ot.network_id}"?`)) return;
  await deleteOperationalTime(ot.id);
  operationalTimes.value = operationalTimes.value.filter((x) => x.id !== ot.id);
}

function enabledDays(ot: OperationalTime) {
  return DAYS.filter((d) => ot[d.flag]).map((d) => d.label).join(", ") || "None";
}

function daySummary(ot: OperationalTime) {
  const parts = DAYS.filter((d) => ot[d.flag]).map(
    (d) => `${ot[d.start]}–${ot[d.end]}`,
  );
  return [...new Set(parts)].join(", ") || "—";
}
</script>
