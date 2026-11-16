<template>
  <div class="space-y-6">
    <div class="flex items-center gap-2">
      <UButton icon="i-lucide-arrow-left" variant="ghost" size="xs" @click="navigateTo('/settings/webfilters')" />
      <h2 class="text-lg font-semibold">{{ wf?.name || "WebFilter" }}</h2>
    </div>

    <div v-if="wf" class="rounded-lg border border-default bg-(--ui-bg) p-4 shadow-sm">
      <div class="grid grid-cols-2 gap-4 text-sm">
        <div>
          <span class="text-(--ui-text-dimmed)">Name:</span>
          <span class="ml-2 font-medium">{{ wf.name }}</span>
        </div>
        <div>
          <span class="text-(--ui-text-dimmed)">Default Block:</span>
          <span class="ml-2">{{ wf.is_default_block ? "Yes" : "No" }}</span>
        </div>
      </div>
    </div>

    <div class="space-y-2">
      <div class="flex items-center justify-between">
        <h3 class="text-base font-semibold">Assigned Members</h3>
        <UButton icon="i-lucide-plus" label="Add Member" size="xs" @click="showAddMember = true" />
      </div>
      <div class="overflow-hidden rounded-lg border border-default bg-(--ui-bg) shadow-sm">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-default bg-(--ui-bg-elevated) text-left text-(--ui-text-dimmed)">
              <th class="px-4 py-3 font-medium">Name</th>
              <th class="px-4 py-3 font-medium">Member ID</th>
              <th class="px-4 py-3 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="m in members"
              :key="m.id"
              class="border-b border-default last:border-0 hover:bg-(--ui-bg-elevated)"
            >
              <td class="px-4 py-3 font-medium">{{ m.member_name }}</td>
              <td class="px-4 py-3 font-mono text-xs text-(--ui-text-dimmed)">{{ m.member_member_id }}</td>
              <td class="px-4 py-3">
                <UButton icon="i-lucide-x" variant="ghost" color="error" size="xs" @click="removeMember(m)" />
              </td>
            </tr>
            <tr v-if="!members.length">
              <td colspan="3" class="px-4 py-6 text-center text-sm text-(--ui-text-dimmed)">No members assigned</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <UModal v-model:open="showAddMember" title="Add Member">
      <template #body>
        <UFormField label="Member ID">
          <UInput v-model="addMemberId" placeholder="Member numeric ID" />
        </UFormField>
      </template>
      <template #footer>
        <div class="flex justify-end gap-2">
          <UButton label="Cancel" color="neutral" variant="outline" @click="showAddMember = false" />
          <UButton label="Add" :loading="adding" @click="addMember" />
        </div>
      </template>
    </UModal>
  </div>
</template>

<script setup lang="ts">
import type { WebFilter, WebFilterMember } from "~/types/api";

const route = useRoute();
const wfId = Number(route.params.id);

const wf = ref<WebFilter | null>(null);
const members = ref<WebFilterMember[]>([]);

try {
  wf.value = await fetchWebfilterDetail(wfId);
  members.value = await fetchWebfilterMembers(wfId);
} catch {
  navigateTo("/settings/webfilters");
}

const showAddMember = ref(false);
const addMemberId = ref("");
const adding = ref(false);

async function addMember() {
  const memberId = Number(addMemberId.value);
  if (!memberId) return;
  adding.value = true;
  try {
    await addWebfilterMember(wfId, memberId);
    members.value = await fetchWebfilterMembers(wfId);
    addMemberId.value = "";
    showAddMember.value = false;
  } catch (e: any) {
    console.error(e);
  } finally {
    adding.value = false;
  }
}

async function removeMember(m: WebFilterMember) {
  if (!confirm(`Remove member "${m.member_name}"?`)) return;
  await removeWebfilterMember(wfId, m.member_id);
  members.value = members.value.filter((x) => x.id !== m.id);
}
</script>
