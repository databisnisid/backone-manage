<template>
  <div class="login-bg min-h-screen flex items-center justify-center relative overflow-hidden">
    <canvas ref="canvasRef" class="particle-canvas" />

    <div class="flex flex-col items-center justify-center relative z-10">
      <div class="flex flex-col items-center mb-8">
        <img src="/images/backone-logo.svg" alt="BackOne" class="w-40 h-40 opacity-90 drop-shadow-2xl object-contain animate-bounce" />
      </div>

      <div class="w-full max-w-md bg-white rounded-lg shadow p-8">
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
          <div class="mb-4 flex items-center">
            <input
              id="remember-me"
              v-model="rememberMe"
              type="checkbox"
              class="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
            />
            <label for="remember-me" class="ml-2 text-sm text-gray-600">Remember me</label>
          </div>

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
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: false });

import { useBackendStore } from "~/stores/backend";
import { useAuthStore } from "~/stores/auth";
import { loginToBackend } from "~/utils/api";

const backend = useBackendStore();
const auth = useAuthStore();
const selectedUrl = ref<string>("");
const username = ref("");
const password = ref("");
const error = ref("");
const loading = ref(false);
const rememberMe = ref(false);

const canvasRef = ref<HTMLCanvasElement | null>(null);

onMounted(() => {
  // Dynamically load Three.js from CDN (avoids bundling)
  const loadThree = new Promise<void>((resolve, reject) => {
    if ((window as any).THREE) return resolve();
    // ponytail: concatenation avoids SFC parser matching <script> literal
    const s = document.createElement("scr" + "ipt");
    s.src = "https://cdnjs.cloudflare.com/ajax/libs/three.js/r124/three.min.js";
    s.async = true;
    s.onload = () => resolve();
    s.onerror = () => reject(new Error("Failed to load Three.js"));
    document.head.appendChild(s);
  });

  loadThree
    .then(() => {
      const THREE = (window as any).THREE;
      if (!THREE || !canvasRef.value) return;

      const canvas = canvasRef.value;
      const renderer = new THREE.WebGLRenderer({ canvas });
      renderer.setPixelRatio(window.devicePixelRatio);
      renderer.setClearColor(new THREE.Color(0x666666));
      renderer.setSize(window.innerWidth, window.innerHeight);

      const scene = new THREE.Scene();
      const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, -1);

      const position = [
        -1.0, -1.0, 0.0,
         1.0, -1.0, 0.0,
        -1.0,  1.0, 0.0,
         1.0, -1.0, 0.0,
        -1.0,  1.0, 0.0,
         1.0,  1.0, 0.0
      ];
      const positions = new THREE.BufferAttribute(new Float32Array(position), 3);
      const geometry = new THREE.BufferGeometry();
      geometry.setAttribute("position", positions);

      const uniforms = {
        resolution: { type: "v2", value: new THREE.Vector2(window.innerWidth, window.innerHeight) },
        time: { type: "f", value: 0.0 },
        xScale: { type: "f", value: 1.0 },
        yScale: { type: "f", value: 0.5 },
        distortion: { type: "f", value: 0.050 }
      };

      const vertexShader = `
        attribute vec3 position;
        void main() {
          gl_Position = vec4(position, 1.0);
        }
      `;

      const fragmentShader = `
        precision highp float;
        uniform vec2 resolution;
        uniform float time;
        uniform float xScale;
        uniform float yScale;
        uniform float distortion;

        void main() {
          vec2 p = (gl_FragCoord.xy * 2.0 - resolution) / min(resolution.x, resolution.y);
          float d = length(p) * distortion;
          float rx = p.x * (1.0 + d);
          float gx = p.x;
          float bx = p.x * (1.0 - d);
          float r = 0.05 / abs(p.y + sin((rx + time) * xScale) * yScale);
          float g = 0.05 / abs(p.y + sin((gx + time) * xScale) * yScale);
          float b = 0.05 / abs(p.y + sin((bx + time) * xScale) * yScale);
          gl_FragColor = vec4(r, g, b, 1.0);
        }
      `;

      const material = new THREE.RawShaderMaterial({
        vertexShader,
        fragmentShader,
        uniforms,
        side: THREE.DoubleSide
      });

      const mesh = new THREE.Mesh(geometry, material);
      scene.add(mesh);

      let raf: number;
      function animate() {
        uniforms.time.value += 0.01;
        renderer.render(scene, camera);
        raf = requestAnimationFrame(animate);
      }

      animate();

      function resize() {
        renderer.setSize(window.innerWidth, window.innerHeight);
        uniforms.resolution.value = new THREE.Vector2(window.innerWidth, window.innerHeight);
      }
      window.addEventListener("resize", resize);
      onUnmounted(() => {
        cancelAnimationFrame(raf);
        window.removeEventListener("resize", resize);
        renderer.dispose();
      });
    });
});

// Initialize backend store on mount
onMounted(async () => {
  await backend.init();
  if (backend.selected) selectedUrl.value = backend.selected.url;
});

// Update backend selection when dropdown changes
watch(selectedUrl, (url) => {
  if (url) backend.select(url);
});

async function handleLogin() {
  if (!selectedUrl.value) return;
  loading.value = true;
  error.value = "";
  try {
    const result = await loginToBackend(username.value, password.value, rememberMe.value);
    if (result.ok) {
      await auth.fetchMe();
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

<style scoped>
.login-bg {
  background: #000;
  overflow: hidden;
}

.particle-canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
  pointer-events: none;
}
</style>
