<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50">
    <div class="w-full max-w-md bg-white rounded-lg shadow p-8">
      <h1 class="text-2xl font-bold text-center mb-6">BackOne Login</h1>

      <!-- Backend selector -->
      <div class="mb-4">
        <label class="block text-sm font-medium text-gray-700 mb-1">Server</label>
        <select
          v-model="selectedUrl"
          class="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option v-for="s in backend.servers" :key="s.url" :value="s.url">
            {{ s.label }} — {{ s.url }}
          </option>
        </select>
      </div>

      <!-- Credentials -->
      <form @submit.prevent="handleLogin">
        <div class="mb-4">
          <label class="block text-sm font-medium text-gray-700 mb-1">Username</label>
          <input
            v-model="username"
            type="text"
            autocomplete="username"
            class="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
        </div>
        <div class="mb-6">
          <label class="block text-sm font-medium text-gray-700 mb-1">Password</label>
          <input
            v-model="password"
            type="password"
            autocomplete="current-password"
            class="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
        </div>

        <div v-if="error" class="mb-4 text-red-600 text-sm">{{ error }}</div>

        <button
          type="submit"
          :disabled="loading || !selectedUrl"
          class="w-full bg-blue-600 text-white py-2 rounded text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
        >
          {{ loading ? "Logging in..." : "Login" }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: false });

import { useBackendStore } from "~/stores/backend";
import { useAuthStore } from "~/stores/auth";
import { loginToBackend } from "~/utils/api";

const backend = useBackendStore();
const auth = useAuthStore();

// Initialize backend store on mount
onMounted(async () => {
  await backend.init();
  if (backend.selected) selectedUrl.value = backend.selected.url;
});

const selectedUrl = ref("");
const username = ref("");
const password = ref("");
const loading = ref(false);
const error = ref("");

// Update backend selection when dropdown changes
watch(selectedUrl, (url) => {
  if (url) backend.select(url);
});

async function handleLogin() {
  if (!selectedUrl.value) return;
  loading.value = true;
  error.value = "";

  try {
    const result = await loginToBackend(username.value, password.value);
    if (result.ok) {
      await auth.fetchMe();
      // Redirect to the originally requested page or dashboard
      const params = new URLSearchParams(window.location.search);
      const next = params.get("next") || "/";
      window.location.href = next;
    } else {
      error.value = "Invalid username or password";
    }
  } catch (e: any) {
    error.value = e.message || "Login failed";
  } finally {
    loading.value = false;
  }
}
</script>
