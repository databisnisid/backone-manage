<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h2 class="text-lg font-semibold">Zabbix Configs</h2>
      <UButton icon="i-lucide-plus" label="Create Config" @click="openCreate" />
    </div>
    <div class="overflow-hidden rounded-lg border border-default bg-(--ui-bg) shadow-sm">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b border-default bg-(--ui-bg-elevated) text-left text-(--ui-text-dimmed)">
            <th class="px-4 py-3 font-medium">Name</th>
            <th class="px-4 py-3 font-medium">URL</th>
            <th class="px-4 py-3 font-medium">Token</th>
            <th class="px-4 py-3 font-medium">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="zc in configs"
            :key="zc.id"
            class="border-b border-default last:border-0 hover:bg-(--ui-bg-elevated)"
          >
            <td class="px-4 py-3 font-medium">{{ zc.name }}</td>
            <td class="px-4 py-3 font-mono text-xs">{{ zc.url }}</td>
            <td class="px-4 py-3 font-mono text-xs text-(--ui-text-dimmed)">{{ zc.token }}</td>
            <td class="px-4 py-3">
              <div class="flex gap-1">
                <UButton icon="i-lucide-pencil" variant="ghost" size="xs" @click="openEdit(zc)" />
                <UButton icon="i-lucide-trash" variant="ghost" color="error" size="xs" @click="remove(zc)" />
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <UModal v-model:open="showModal" :title="editing ? 'Edit Config' : 'Create Config'">
      <template #body>
        <UForm :state="form" @submit="save">
          <UFormField label="Name" required>
            <UInput v-model="form.name" placeholder="Config name" />
          </UFormField>
          <UFormField label="Zabbix API URL" required class="mt-3">
            <UInput v-model="form.url" placeholder="https://zabbix.example.com/api_jsonrpc.php" />
          </UFormField>
          <UFormField label="Token" required class="mt-3">
            <UInput v-model="form.token" placeholder="API token" />
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
import type { ZabbixConfig } from "~/types/api";

const configs = ref<ZabbixConfig[]>([]);
configs.value = await fetchZabbixConfigs();

const showModal = ref(false);
const editing = ref<ZabbixConfig | null>(null);
const saving = ref(false);
const form = reactive({ name: "", url: "", token: "" });

function openCreate() {
  editing.value = null;
  form.name = "";
  form.url = "";
  form.token = "";
  showModal.value = true;
}
function openEdit(zc: ZabbixConfig) {
  editing.value = zc;
  form.name = zc.name;
  form.url = zc.url;
  form.token = "";
  showModal.value = true;
}
async function save() {
  saving.value = true;
  try {
    if (editing.value) {
      const payload: Record<string, string> = { name: form.name, url: form.url };
      if (form.token && form.token !== "****") payload.token = form.token;
      await updateZabbixConfig(editing.value.id, payload);
    } else {
      await createZabbixConfig({ ...form });
    }
    configs.value = await fetchZabbixConfigs();
    showModal.value = false;
  } catch (e: any) {
    console.error(e);
  } finally {
    saving.value = false;
  }
}
async function remove(zc: ZabbixConfig) {
  if (!confirm(`Delete "${zc.name}"?`)) return;
  await deleteZabbixConfig(zc.id);
  configs.value = configs.value.filter((c) => c.id !== zc.id);
}
</script>
