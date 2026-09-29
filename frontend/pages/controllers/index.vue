<template>
  <UDashboardPanel id="controllers">
    <template #header>
      <UDashboardNavbar title="Controllers">
        <template #leading>
          <UDashboardSidebarCollapse />
        </template>
        <template #trailing>
          <UButton
            icon="i-lucide-plus"
            label="Create Controller"
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
          placeholder="Search controllers…"
          class="max-w-sm"
        />
        <p class="text-xs text-(--ui-text-dimmed)">Showing {{ controllers.length }} controllers</p>
        <div class="overflow-hidden rounded-lg border border-default bg-(--ui-bg) shadow-sm">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-default bg-(--ui-bg-elevated) text-left text-(--ui-text-dimmed)">
                <th class="px-4 py-3 font-medium">Name</th>
                <th class="px-4 py-3 font-medium">Description</th>
                <th class="px-4 py-3 font-medium">URI</th>
                <th class="px-4 py-3 font-medium">Token</th>
                <th class="px-4 py-3 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="c in filtered"
                :key="c.id"
                class="border-b border-default last:border-0 hover:bg-(--ui-bg-elevated)"
              >
                <td class="px-4 py-3 font-medium">{{ c.name }}</td>
                <td class="px-4 py-3 text-(--ui-text-dimmed)">{{ c.description || "—" }}</td>
                <td class="px-4 py-3 font-mono text-xs">{{ c.uri }}</td>
                <td class="px-4 py-3 font-mono text-xs text-(--ui-text-dimmed)">{{ c.token }}</td>
                <td class="px-4 py-3 flex gap-1">
                  <UButton icon="i-lucide-pencil" variant="ghost" size="xs" @click="openEdit(c)" />
                  <UButton icon="i-lucide-trash-2" variant="ghost" color="error" size="xs" @click="remove(c)" />
                </td>
              </tr>
            </tbody>
          </table>
          <div v-if="filtered.length === 0" class="p-6 text-sm text-(--ui-text-dimmed)">No controllers.</div>
        </div>
      </div>

      <UModal v-model:open="modalOpen" :title="editing ? 'Edit Controller' : 'Create Controller'">
        <template #body>
          <UForm :state="form" @submit="submit">
            <UFormField label="Name" name="name" required>
              <UInput v-model="form.name" placeholder="Controller name" />
            </UFormField>
            <UFormField label="Description" name="description">
              <UInput v-model="form.description" placeholder="Optional description" />
            </UFormField>
            <UFormField label="URI" name="uri" required>
              <UInput v-model="form.uri" placeholder="http://controller:9993" />
            </UFormField>
            <UFormField label="Token" name="token" required>
              <UInput v-model="form.token" placeholder="ZeroTier auth token" />
            </UFormField>
            <div v-if="error" class="mt-2 p-2 rounded bg-red-50 text-red-700 text-sm dark:bg-red-900/20 dark:text-red-400">{{ error }}</div>
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
import type { Controller } from "~/types/api";

const auth = useAuthStore();
const loggedIn = await requireAuth();
if (!loggedIn || !auth.isSuperuser) {
  window.location.assign("/");
}

const search = ref("");
const controllers = ref<Controller[]>([]);
if (loggedIn && auth.isSuperuser) {
  controllers.value = await fetchControllers();
}

const filtered = computed(() => {
  const q = search.value.toLowerCase();
  return controllers.value.filter(
    (c) =>
      c.name.toLowerCase().includes(q) ||
      c.description?.toLowerCase().includes(q) ||
      c.uri.toLowerCase().includes(q),
  );
});

// Modal state
const modalOpen = ref(false);
const editing = ref<Controller | null>(null);
const saving = ref(false);
const error = ref("");
const form = reactive({ name: "", description: "", uri: "", token: "" });

function openCreate() {
  editing.value = null;
  form.name = "";
  form.description = "";
  form.uri = "";
  form.token = "";
  error.value = "";
  modalOpen.value = true;
}

async function openEdit(c: Controller) {
  editing.value = c;
  // Fetch detail for full token
  const detail = await fetchControllerDetail(c.id);
  form.name = detail.name;
  form.description = detail.description || "";
  form.uri = detail.uri;
  form.token = detail.token;
  error.value = "";
  modalOpen.value = true;
}

async function submit() {
  saving.value = true;
  error.value = "";
  try {
    if (editing.value) {
      await updateController(editing.value.id, { ...form });
    } else {
      await createController({ ...form });
    }
    modalOpen.value = false;
    controllers.value = await fetchControllers();
  } catch (e: any) {
    const data = e?.data || e;
    error.value = typeof data === "string" ? data : data?.error || "Save failed";
  } finally {
    saving.value = false;
  }
}

async function remove(c: Controller) {
  if (!confirm(`Delete controller "${c.name}"?`)) return;
  await deleteController(c.id);
  controllers.value = controllers.value.filter((x) => x.id !== c.id);
}
</script>
