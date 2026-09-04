<script setup lang="ts">
import type { NavigationMenuItem } from "@nuxt/ui";
import backoneLogo from "~/assets/images/backone-logo.svg";

const auth = useAuthStore();
const open = ref(false);

const links = [[
  { label: "Dashboard", icon: "i-lucide-house", to: "/", onSelect: () => onSelect() },
  { label: "Members", icon: "i-lucide-users", to: "/members", onSelect: () => onSelect() },
  { label: "Networks", icon: "i-lucide-network", to: "/networks", onSelect: () => onSelect() },
]] satisfies NavigationMenuItem[][];

function onSelect() {
  open.value = false;
}

async function logout() {
  const csrf = (document.querySelector('meta[name="csrf-token"]') as HTMLMetaElement | null)?.content ?? "";
  try {
    await fetch("/accounts/logout/", {
      method: "POST",
      credentials: "same-origin",
      headers: { "X-CSRFToken": csrf },
      redirect: "manual",
    });
  } catch {
    // fall through — clear local state either way
  }
  auth.clear();
  window.location.assign("/login/");
}
</script>

<template>
  <UDashboardGroup unit="rem">
    <UDashboardSidebar
      id="backone"
      v-model:open="open"
      collapsible
      resizable
      class="bg-elevated/25"
      :ui="{ footer: 'lg:border-t lg:border-default' }"
    >
      <template #header="{ collapsed }">
        <NuxtLink to="/" class="flex items-center gap-2 px-2 py-1 font-semibold">
          <span class="flex h-7 w-7 shrink-0 items-center justify-center overflow-hidden rounded-md bg-(--ui-elevated)">
            <img :src="backoneLogo" alt="BackOne" class="h-7 w-7 object-contain" />
          </span>
          <span v-if="!collapsed" class="text-sm">BackOne</span>
        </NuxtLink>
      </template>

      <template #default>
        <UNavigationMenu :items="links[0]" orientation="vertical" />
      </template>

      <template #footer>
        <UDropdownMenu
          :items="[[{ type: 'label', label: auth.orgName || (auth.isSuperuser ? 'Superuser' : 'Account') }], [{ label: 'Log out', icon: 'i-lucide-log-out', onSelect: logout }]]"
          :content="{ align: 'center' }"
        >
          <UButton
            :label="auth.orgName || (auth.isSuperuser ? 'Superuser' : 'Account')"
            color="neutral"
            variant="ghost"
            block
            trailing-icon="i-lucide-chevrons-up-down"
            class="data-[state=open]:bg-elevated"
          />
        </UDropdownMenu>
      </template>
    </UDashboardSidebar>

    <slot />
  </UDashboardGroup>
</template>