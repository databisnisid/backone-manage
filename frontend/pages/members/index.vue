<template>
  <UDashboardPanel id="members">
    <template #header>
      <UDashboardNavbar title="Members">
        <template #leading>
          <UDashboardSidebarCollapse />
        </template>
        <template #trailing>
          <UButton
            v-if="canAdd"
            icon="i-lucide-plus"
            label="Add Member"
            @click="openAdopt"
          />
        </template>
      </UDashboardNavbar>
    </template>

    <template #body>
      <div class="space-y-4 p-4">
        <UInput
          v-model="search"
          icon="i-lucide-search"
          placeholder="Search by name, member ID, or IP…"
          class="max-w-sm"
        />
        <p class="text-xs text-(--ui-text-dimmed)">Showing {{ members.length }} members</p>
        <div class="overflow-hidden rounded-lg border border-default bg-(--ui-bg) shadow-sm">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-default bg-(--ui-bg-elevated) text-left text-(--ui-text-dimmed)">
                <th class="px-4 py-3 font-medium">Name</th>
                <th class="px-4 py-3 font-medium">Member ID</th>
                <th class="px-4 py-3 font-medium">IP</th>
                <th class="px-4 py-3 font-medium">Status</th>
                <th class="px-4 py-3 font-medium">Problem</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="m in filteredMembers"
                :key="m.member_id"
                class="cursor-pointer border-b border-default last:border-0 hover:bg-(--ui-bg-elevated)"
                @click="navigateToMember(m.member_id)"
              >
                <td class="px-4 py-3 font-medium">{{ m.name }}</td>
                <td class="px-4 py-3 font-mono text-xs text-(--ui-text-dimmed)">{{ m.member_id }}</td>
                <td class="px-4 py-3 font-mono text-xs text-(--ui-text-dimmed)">{{ m.ipaddress || "—" }}</td>
                <td class="px-4 py-3">
                  <UBadge
                    :color="m.is_online ? 'success' : 'neutral'"
                    variant="subtle"
                    size="sm"
                  >
                    <template #leading>
                      <span :class="['size-1.5 rounded-full', m.is_online ? 'bg-emerald-500' : 'bg-gray-400']" />
                    </template>
                    {{ m.is_online ? "online" : "offline" }}
                  </UBadge>
                </td>
                <td class="px-4 py-3">
                  <UBadge v-if="m.is_problem" color="error" variant="subtle" size="sm">
                    {{ m.problem_string }}
                  </UBadge>
                  <span v-else class="text-(--ui-text-dimmed)">—</span>
                </td>
              </tr>
            </tbody>
          </table>
          <div v-if="filteredMembers.length === 0" class="p-6 text-sm text-(--ui-text-dimmed)">No members.</div>
        </div>
      </div>

      <UModal v-model:open="modalOpen" title="Add Member">
        <template #body>
          <UForm :state="form" @submit="submit">
            <UFormField label="Network" name="network_id" required>
              <USelect v-model="form.network_id" :items="networkItems" @update:model-value="loadOptions" />
            </UFormField>
            <UFormField label="Controller member" name="member_id" required>
              <USelect
                v-model="form.member_id"
                :items="memberItems"
                :loading="loadingOptions"
                placeholder="Select a member that joined this network…"
              />
            </UFormField>
            <UFormField label="Name" name="name">
              <UInput v-model="form.name" placeholder="Defaults to NET-<network> MEMBER-<id>" />
            </UFormField>
            <div v-if="selectedOption" class="mt-2 text-xs text-(--ui-text-dimmed)">
              Controller says:
              {{ selectedOption.authorized ? "authorized" : "pending authorization" }}
              <template v-if="selectedOption.ipaddress"> · {{ selectedOption.ipaddress }}</template>
            </div>
            <div v-if="error" class="mt-2 p-2 rounded bg-red-50 text-red-700 text-sm dark:bg-red-900/20 dark:text-red-400">{{ error }}</div>
            <div class="flex justify-end gap-2 pt-4">
              <UButton variant="outline" @click="modalOpen = false">Cancel</UButton>
              <UButton type="submit" :loading="saving" :disabled="!form.network_id || !form.member_id">
                Add
              </UButton>
            </div>
          </UForm>
        </template>
      </UModal>
    </template>
  </UDashboardPanel>
</template>

<script setup lang="ts">
import type { Member, Network, ControllerMemberOption } from "~/types/api";

const members = ref<Member[]>([]);
const search = ref("");
const auth = useAuthStore();
await requireAuth();
if (auth.loggedIn) {
  members.value = await api<Member[]>("/api/app/members/");
}
const filteredMembers = computed(() => {
  const q = search.value.trim().toLowerCase();
  if (!q) return members.value;
  return members.value.filter(
    (m) =>
      m.name.toLowerCase().includes(q) ||
      m.member_id.toLowerCase().includes(q) ||
      (m.ipaddress || "").toLowerCase().includes(q),
  );
});
function navigateToMember(id: string) {
  navigateTo(`/members/${encodeURIComponent(id)}`);
}

// Capability comes from the server (§C); the view re-checks, so this only
// keeps a dead button off the screen.
const canAdd = computed(() => auth.me?.permissions?.members_add === true);

const modalOpen = ref(false);
const saving = ref(false);
const loadingOptions = ref(false);
const error = ref("");
const form = reactive({ network_id: "", member_id: "", name: "" });
const networks = ref<Network[]>([]);
const options = ref<ControllerMemberOption[]>([]);

const networkItems = computed(() =>
  networks.value.map((n) => ({ label: n.name, value: n.network_id })),
);
const memberItems = computed(() =>
  options.value.map((o) => ({
    label: `${o.member_id}${o.authorized ? "" : " (pending)"}${o.ipaddress ? ` · ${o.ipaddress}` : ""}`,
    value: o.member_id,
  })),
);
const selectedOption = computed(() =>
  options.value.find((o) => o.member_id === form.member_id),
);

async function openAdopt() {
  error.value = "";
  form.member_id = "";
  form.name = "";
  options.value = [];
  modalOpen.value = true;
  if (!networks.value.length) {
    networks.value = await api<Network[]>("/api/app/networks/");
  }
  if (!form.network_id && networks.value.length) {
    form.network_id = networks.value[0].network_id;
    await loadOptions();
  }
}

async function loadOptions() {
  form.member_id = "";
  options.value = [];
  if (!form.network_id) return;
  loadingOptions.value = true;
  error.value = "";
  try {
    options.value = await fetchControllerMembers(form.network_id);
  } catch (e: any) {
    error.value = e?.data?.error || "Could not reach the controller";
  } finally {
    loadingOptions.value = false;
  }
}

async function submit() {
  saving.value = true;
  error.value = "";
  try {
    const body: any = { network_id: form.network_id, member_id: form.member_id };
    if (form.name) body.name = form.name;
    await createMember(body);
    modalOpen.value = false;
    members.value = await api<Member[]>("/api/app/members/");
  } catch (e: any) {
    const data = e?.data || e;
    const rule = data?.rule;
    error.value =
      rule === "superuser_no_member_write"
        ? "A superuser cannot write members (platform operator, not tenant)."
        : typeof data?.error === "string"
          ? data.error
          : data?.error
            ? JSON.stringify(data.error)
            : "Add failed";
  } finally {
    saving.value = false;
  }
}
</script>
