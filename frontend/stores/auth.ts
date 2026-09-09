import { defineStore } from "pinia";
import type { MeResponse } from "~/types/api";
import { useBackendStore } from "~/stores/backend";
import { api } from "~/utils/api";

export const useAuthStore = defineStore("auth", {
  state: () => ({
    me: null as MeResponse | null,
    loaded: false,
  }),
  getters: {
    loggedIn: (s) => !!s.me,
    orgName: (s) => s.me?.organization?.name ?? "",
    isSuperuser: (s) => !!s.me?.is_superuser,
  },
  actions: {
    async fetchMe() {
      const backend = useBackendStore();
      await backend.ensureInit();
      if (!backend.selected) {
        this.me = null;
        this.loaded = true;
        return;
      }
      try {
        this.me = await api<MeResponse>("/api/app/me/");
      } catch {
        this.me = null;
      } finally {
        this.loaded = true;
      }
    },
    clear() {
      this.me = null;
      this.loaded = true;
    },
  },
});

/** Router guard — redirect unauthenticated users to login preserving next. */
export async function requireAuth(): Promise<boolean> {
  const auth = useAuthStore();
  if (!auth.loaded) {
    await auth.fetchMe();
  }
  if (!auth.loggedIn) redirectToLogin();
  return auth.loggedIn;
}

function redirectToLogin() {
  const next = encodeURIComponent(window.location.pathname + window.location.search);
  window.location.assign(`/login/?next=${next}`);
}
