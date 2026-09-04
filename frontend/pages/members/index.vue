<template>
  <UDashboardPanel id="members">
    <template #header>
      <UDashboardNavbar title="Members">
        <template #leading>
          <UDashboardSidebarCollapse />
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
    </template>
  </UDashboardPanel>
</template>

<script setup lang="ts">
import type { Member } from "~/types/api";

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
</script>