<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h2 class="text-lg font-semibold">Headscale Users</h2>
      <UButton icon="i-lucide-plus" label="Create User" @click="openCreate" />
    </div>
    <div class="overflow-hidden rounded-lg border border-default bg-(--ui-bg) shadow-sm">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b border-default bg-(--ui-bg-elevated) text-left text-(--ui-text-dimmed)">
            <th class="px-4 py-3 font-medium">Name</th>
            <th class="px-4 py-3 font-medium">Description</th>
            <th class="px-4 py-3 font-medium">Created</th>
            <th class="px-4 py-3 font-medium">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="u in users"
            :key="u.id"
            class="border-b border-default last:border-0 hover:bg-(--ui-bg-elevated)"
          >
            <td class="px-4 py-3 font-medium">{{ u.name }}</td>
            <td class="px-4 py-3 text-(--ui-text-dimmed)">{{ u.description || "—" }}</td>
            <td class="px-4 py-3 text-xs text-(--ui-text-dimmed)">{{ u.created_at ? new Date(u.created_at).toLocaleDateString() : "—" }}</td>
            <td class="px-4 py-3">
              <div class="flex gap-1">
                <UButton icon="i-lucide-pencil" variant="ghost" size="xs" @click="openEdit(u)" />
                <UButton icon="i-lucide-trash" variant="ghost" color="error" size="xs" @click="remove(u)" />
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <UModal v-model:open="showModal" :title="editing ? 'Edit User' : 'Create User'">
      <template #body>
        <UForm :state="form" @submit="save">
          <UFormField label="Name" required>
            <UInput v-model="form.name" placeholder="Lowercase alphanumeric (dots/hyphens)" />
          </UFormField>
          <UFormField label="Description" class="mt-3">
            <UInput v-model="form.description" placeholder="Optional description" />
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
import type { HSUser } from "~/types/api";

const auth = useAuthStore();
const users = ref<HSUser[]>([]);
users.value = await fetchHSUsers();

const showModal = ref(false);
const editing = ref<HSUser | null>(null);
const saving = ref(false);
const form = reactive({ name: "", description: "" });

function openCreate() {
  editing.value = null;
  form.name = "";
  form.description = "";
  showModal.value = true;
}
function openEdit(u: HSUser) {
  editing.value = u;
  form.name = u.name;
  form.description = u.description || "";
  showModal.value = true;
}
async function save() {
  saving.value = true;
  try {
    if (editing.value) {
      await updateHSUser(editing.value.id, { ...form });
    } else {
      await createHSUser({ ...form, organization: auth.me?.organization?.id ?? 0 });
    }
    users.value = await fetchHSUsers();
    showModal.value = false;
  } catch (e: any) {
    console.error(e);
  } finally {
    saving.value = false;
  }
}
async function remove(u: HSUser) {
  if (!confirm(`Delete user "${u.name}"?`)) return;
  await deleteHSUser(u.id);
  users.value = users.value.filter((x) => x.id !== u.id);
}
</script>
