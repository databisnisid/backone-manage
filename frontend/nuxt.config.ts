import tailwindcss from "@tailwindcss/vite";
import { eventHandler, getRequestURL } from "h3";
import { createProxyServer } from "http-proxy";

const DJANGO = "http://127.0.0.1:8008";

function djangoProxy(event: any) {
  const target = DJANGO + getRequestURL(event).pathname;
  return new Promise<void>((resolve, reject) => {
    const proxy = createProxyServer({
      target,
      changeOrigin: true,
      ignorePath: true,
    });
    proxy.once("error", reject);
    proxy.web(event.node.req, event.node.res, {}, () => {});
    proxy.once("proxyRes", () => {
      resolve();
    });
  });
}

export default defineNuxtConfig({
  compatibilityDate: "2026-09-04",
  ssr: false,
  devtools: false,
  app: {
    baseURL: "/app/",
  },
  css: ["~/assets/css/main.css"],
  modules: ["@pinia/nuxt", "@nuxt/ui"],
  colorMode: {
    preference: "light",
  },
  runtimeConfig: {
    public: {
      apiBase: "",
      googleMapsApiKey: "",
      mapCenter: "",
      mapZoom: "",
      mapRefreshInterval: "300",
    },
  },
  nitro: {
    devHandlers: [
      { route: "/api", handler: djangoProxy },
      { route: "/accounts", handler: djangoProxy },
      { route: "/two", handler: djangoProxy },
      { route: "/login", handler: djangoProxy },
      { route: "/logout", handler: djangoProxy },
      { route: "/custom", handler: djangoProxy },
      { route: "/documents", handler: djangoProxy },
      { route: "/static", handler: djangoProxy },
    ],
  },
  vite: {
    plugins: [tailwindcss()],
  },
})