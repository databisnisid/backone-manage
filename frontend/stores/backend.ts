import { defineStore } from "pinia";

interface BackendServer {
  label: string;
  url: string;
}

const STORAGE_KEY = "selectedBackend";

export const useBackendStore = defineStore("backend", {
  state: () => ({
    servers: [] as BackendServer[],
    selected: null as BackendServer | null,
    _initPromise: null as Promise<void> | null,
  }),
  getters: {
    apiBase: (s) => s.selected?.url ?? "",
    isLoggedIn: (s) => !!s.selected,
  },
  actions: {
    /** Fetch server list from runtime config.json, then restore or auto-select. */
    async init() {
      try {
        const base = useRouter().options.base || "/";
        const res = await fetch(`${base}config.json`);
        if (res.ok) {
          this.servers = await res.json();
        }
      } catch {
        this.servers = [];
      }
      // Restore last selection from localStorage
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const match = this.servers.find((s) => s.url === saved);
        if (match) this.selected = match;
      }
      // Single-server deployment: auto-select if nothing saved
      if (!this.selected && this.servers.length === 1) {
        this.selected = this.servers[0];
      }
    },
    /** Ensure init has run (idempotent, caches promise). */
    async ensureInit() {
      if (this._initPromise) return this._initPromise;
      this._initPromise = this.init();
      return this._initPromise;
    },
    select(url: string) {
      const server = this.servers.find((s) => s.url === url);
      if (!server) throw new Error(`Unknown backend: ${url}`);
      this.selected = server;
      localStorage.setItem(STORAGE_KEY, server.url);
    },
    clear() {
      this.selected = null;
      localStorage.removeItem(STORAGE_KEY);
    },
  },
});
