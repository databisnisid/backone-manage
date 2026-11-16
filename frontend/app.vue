<script setup lang="ts">
import backoneLogo from "~/assets/images/backone-logo.svg";

const colorMode = useColorMode();
const color = computed(() => (colorMode.value === "dark" ? "#1b1718" : "white"));

useHead({
  link: [{ rel: "icon", type: "image/svg+xml", href: backoneLogo }],
  meta: [
    { charset: "utf-8" },
    { name: "viewport", content: "width=device-width, initial-scale=1" },
    { key: "theme-color", name: "theme-color", content: color },
  ],
});
</script>

<template>
  <UApp>
    <NuxtLayout>
      <NuxtPage />
    </NuxtLayout>
  </UApp>
</template>