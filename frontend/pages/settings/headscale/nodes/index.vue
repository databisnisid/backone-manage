<template>
  <div class="space-y-4">
    <h2 class="text-lg font-semibold">Headscale Nodes</h2>
    <div class="overflow-hidden rounded-lg border border-default bg-(--ui-bg) shadow-sm">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b border-default bg-(--ui-bg-elevated) text-left text-(--ui-text-dimmed)">
            <th class="px-4 py-3 font-medium">Name</th>
            <th class="px-4 py-3 font-medium">Node Key</th>
            <th class="px-4 py-3 font-medium">Addresses</th>
            <th class="px-4 py-3 font-medium">Created</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="n in nodes"
            :key="n.id"
            class="border-b border-default last:border-0 hover:bg-(--ui-bg-elevated)"
          >
            <td class="px-4 py-3 font-medium">{{ n.name }}</td>
            <td class="px-4 py-3 font-mono text-xs text-(--ui-text-dimmed)">{{ n.node_key }}</td>
            <td class="px-4 py-3 font-mono text-xs">{{ n.addresses }}</td>
            <td class="px-4 py-3 text-xs text-(--ui-text-dimmed)">{{ n.created_at ? new Date(n.created_at).toLocaleDateString() : "—" }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { HSNode } from "~/types/api";

const nodes = ref<HSNode[]>([]);
nodes.value = await fetchHSNodes();
</script>
