<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h2 class="text-lg font-semibold">Headscale Preauth Keys</h2>
      <UButton icon="i-lucide-plus" label="Create Key" @click="openCreate" />
    </div>
    <div class="overflow-hidden rounded-lg border border-default bg-(--ui-bg) shadow-sm">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b border-default bg-(--ui-bg-elevated) text-left text-(--ui-text-dimmed)">
            <th class="px-4 py-3 font-medium">Key</th>
            <th class="px-4 py-3 font-medium">Reusable</th>
            <th class="px-4 py-3 font-medium">Ephemeral</th>
            <th class="px-4 py-3 font-medium">Used</th>
            <th class="px-4 py-3 font-medium">Expires</th>
            <th class="px-4 py-3 font-medium">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="k in keys"
            :key="k.id"
            class="border-b border-default last:border-0 hover:bg-(--ui-bg-elevated)"
          >
            <td class="px-4 py-3 font-mono text-xs">{{ k.key }}</td>
            <td class="px-4 py-3">{{ k.is_reusable ? "Yes" : "No" }}</td>
            <td class="px-4 py-3">{{ k.is_ephemeral ? "Yes" : "No" }}</td>
            <td class="px-4 py-3">{{ k.is_used ? "Yes" : "No" }}</td>
            <td class="px-4 py-3 text-xs text-(--ui-text-dimmed)">{{ k.expiration ? new Date(k.expiration).toLocaleDateString() : "—" }}</td>
            <td class="px-4 py-3">
              <UButton icon="i-lucide-trash" variant="ghost" color="error" size="xs" @click="remove(k)" />
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <UModal v-model:open="showModal" title="Create Preauth Key">
      <template #body>
        <UForm :state="form" @submit="save">
          <UFormField label="HS User ID" required>
            <UInput v-model.number="form.hs_user_id" type="number" placeholder="HS Users table ID" />
          </UFormField>
          <div class="mt-3 flex gap-4">
            <UFormField label="Reusable">
              <USwitch v-model="form.is_reusable" />
            </UFormField>
            <UFormField label="Ephemeral">
              <USwitch v-model="form.is_ephemeral" />
            </UFormField>
          </div>
        </UForm>
      </template>
      <template #footer>
        <div class="flex justify-end gap-2">
          <UButton label="Cancel" color="neutral" variant="outline" @click="showModal = false" />
          <UButton label="Create" :loading="saving" @click="save" />
        </div>
      </template>
    </UModal>
  </div>
</template>

<script setup lang="ts">
import type { HSPreauthkey } from "~/types/api";

const keys = ref<HSPreauthkey[]>([]);
keys.value = await fetchHSPreauthkeys();

const showModal = ref(false);
const saving = ref(false);
const form = reactive({ hs_user_id: 0, is_reusable: false, is_ephemeral: false });

function openCreate() {
  form.hs_user_id = 0;
  form.is_reusable = false;
  form.is_ephemeral = false;
  showModal.value = true;
}
async function save() {
  if (!form.hs_user_id) return;
  saving.value = true;
  try {
    await createHSPreauthkey({ ...form });
    keys.value = await fetchHSPreauthkeys();
    showModal.value = false;
  } catch (e: any) {
    console.error(e);
  } finally {
    saving.value = false;
  }
}
async function remove(k: HSPreauthkey) {
  if (!confirm("Delete this preauth key?")) return;
  await deleteHSPreauthkey(k.id);
  keys.value = keys.value.filter((x) => x.id !== k.id);
}
</script>
