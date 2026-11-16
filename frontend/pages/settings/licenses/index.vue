<template>
  <div class="space-y-4">
    <h2 class="text-lg font-semibold">Licenses</h2>
    <div class="overflow-hidden rounded-lg border border-default bg-(--ui-bg) shadow-sm">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b border-default bg-(--ui-bg-elevated) text-left text-(--ui-text-dimmed)">
            <th class="px-4 py-3 font-medium">Node ID</th>
            <th class="px-4 py-3 font-medium">Org UUID</th>
            <th class="px-4 py-3 font-medium">Block Rule</th>
            <th class="px-4 py-3 font-medium">Created</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="l in licenses"
            :key="l.id"
            class="border-b border-default last:border-0 hover:bg-(--ui-bg-elevated)"
          >
            <td class="px-4 py-3 font-mono text-xs font-medium">{{ l.node_id }}</td>
            <td class="px-4 py-3 font-mono text-xs text-(--ui-text-dimmed)">{{ l.organization_uuid || "—" }}</td>
            <td class="px-4 py-3">{{ l.is_block_rule ? "Yes" : "No" }}</td>
            <td class="px-4 py-3 text-xs text-(--ui-text-dimmed)">{{ l.created_at ? new Date(l.created_at).toLocaleDateString() : "—" }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { LicenseItem } from "~/types/api";

const licenses = ref<LicenseItem[]>([]);
licenses.value = await fetchLicenses();
</script>
