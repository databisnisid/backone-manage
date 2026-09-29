<template>
  <UDashboardPanel id="settings">
    <template #header>
      <UDashboardNavbar title="Settings">
        <template #leading>
          <UDashboardSidebarCollapse />
        </template>
      </UDashboardNavbar>
    </template>

    <template #body>
      <div class="flex gap-6 p-4">
        <nav class="w-48 shrink-0 space-y-1">
          <NuxtLink
            v-for="item in navItems"
            :key="item.to"
            :to="item.to"
            class="flex items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors hover:bg-(--ui-bg-elevated)"
            active-class="bg-(--ui-bg-elevated) font-medium text-(--ui-text-highlighted)"
          >
            <UIcon :name="item.icon" class="size-4" />
            {{ item.label }}
          </NuxtLink>
        </nav>
        <div class="min-w-0 flex-1">
          <NuxtPage />
        </div>
      </div>
    </template>
  </UDashboardPanel>
</template>

<script setup lang="ts">
const auth = useAuthStore();
const loggedIn = await requireAuth();
if (!loggedIn) {
  window.location.assign("/");
}

const navItems = computed(() => {
  const items = [
    { label: "WebFilters", icon: "i-lucide-shield", to: "/settings/webfilters" },
    { label: "Monitor", icon: "i-lucide-activity", to: "/settings/monitor" },
    { label: "Operational Time", icon: "i-lucide-clock", to: "/settings/operational-time" },
    { label: "Headscale Users", icon: "i-lucide-users", to: "/settings/headscale/users" },
    { label: "Headscale Nodes", icon: "i-lucide-server", to: "/settings/headscale/nodes" },
    { label: "Headscale Keys", icon: "i-lucide-key", to: "/settings/headscale/preauthkeys" },
  ];
  if (auth.isSuperuser) {
    items.push(
      { label: "Zabbix", icon: "i-lucide-bar-chart", to: "/settings/zabbix" },
      { label: "Licenses", icon: "i-lucide-key", to: "/settings/licenses" },
      { label: "Features", icon: "i-lucide-sliders", to: "/settings/features" },
      { label: "Devices", icon: "i-lucide-smartphone", to: "/settings/devices" },
    );
  }
  return items;
});
</script>
