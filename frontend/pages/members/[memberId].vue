<template>
  <UDashboardPanel id="member-detail">
    <template #header>
      <UDashboardNavbar :title="data?.member?.name || 'Member'">
        <template #leading>
          <UDashboardSidebarCollapse />
        </template>
        <template #trailing>
          <UButton
            v-if="canChange"
            icon="i-lucide-pencil"
            label="Edit"
            variant="ghost"
            @click="openEdit"
          />
          <UButton
            v-if="canDelete"
            icon="i-lucide-trash-2"
            label="Delete"
            color="error"
            variant="ghost"
            @click="remove"
          />
        </template>
      </UDashboardNavbar>
    </template>

    <template #body>
      <div v-if="data" class="grid gap-4 p-4">

        <!-- Status banner -->
        <div
          class="rounded-lg border p-3 text-sm font-medium"
          :class="data.member.is_online ? 'border-emerald-700/40 bg-emerald-500/10 text-emerald-600' : 'border-default bg-(--ui-bg) text-(--ui-text-dimmed)'"
        >
          {{ onlineLabel }}
          <template v-if="data.member.is_problem"> · Open problem</template>
        </div>

        <div class="grid gap-4 lg:grid-cols-2">
          <!-- Overview -->
          <div class="rounded-lg border border-default bg-(--ui-bg) p-5 shadow-sm">
            <h2 class="text-sm font-medium text-(--ui-text-dimmed)">Overview</h2>
            <dl class="mt-3 grid grid-cols-2 gap-4 text-sm">
              <div>
                <dt class="text-(--ui-text-dimmed)">Member ID</dt>
                <dd class="mt-0.5 font-mono text-xs">{{ data.member.member_id }}</dd>
              </div>
              <div>
                <dt class="text-(--ui-text-dimmed)">IP</dt>
                <dd class="mt-0.5 font-mono text-xs">{{ displayIp }}</dd>
              </div>
              <div>
                <dt class="text-(--ui-text-dimmed)">Status</dt>
                <dd class="mt-0.5">{{ data.member.is_online ? "online" : "offline" }}</dd>
              </div>
              <div>
                <dt class="text-(--ui-text-dimmed)">Network</dt>
                <dd class="mt-0.5 font-mono text-xs">{{ data.member.network?.name || data.member.network?.network_id || "—" }}</dd>
              </div>
              <div>
                <dt class="text-(--ui-text-dimmed)">Location</dt>
                <dd class="mt-0.5">{{ data.member.location || "—" }}</dd>
              </div>
              <div>
                <dt class="text-(--ui-text-dimmed)">Address</dt>
                <dd class="mt-0.5">{{ data.member.address || "—" }}</dd>
              </div>
              <div>
                <dt class="text-(--ui-text-dimmed)">Organization</dt>
                <dd class="mt-0.5">{{ data.member.organization || "—" }}</dd>
              </div>
            </dl>

            <!-- Timeline merged into Overview -->
            <dl class="mt-3 grid grid-cols-2 gap-4 text-sm">
              <div>
                <dt class="text-(--ui-text-dimmed)">First seen</dt>
                <dd class="mt-0.5">{{ data.member.created_at || "—" }}</dd>
              </div>
              <div>
                <dt class="text-(--ui-text-dimmed)">Last update</dt>
                <dd class="mt-0.5">{{ data.member.updated_at || "—" }}</dd>
              </div>
              <div>
                <dt class="text-(--ui-text-dimmed)">Online since</dt>
                <dd class="mt-0.5">{{ data.member.online_at || "—" }}</dd>
              </div>
              <div>
                <dt class="text-(--ui-text-dimmed)">Offline since</dt>
                <dd class="mt-0.5">{{ data.member.offline_at || "—" }}</dd>
              </div>
              <div>
                <dt class="text-(--ui-text-dimmed)">Member code</dt>
                <dd class="mt-0.5 font-mono text-xs">{{ data.member.member_code || "—" }}</dd>
              </div>
            </dl>
          </div>

          <!-- Location map (right of Overview, compact) -->
          <div class="flex flex-col rounded-lg border border-default bg-(--ui-bg) p-5 shadow-sm lg:h-full">
            <h2 class="text-sm font-medium text-(--ui-text-dimmed)">Location</h2>
            <div v-if="data.member.lat != null && data.member.lng != null" class="mt-3 lg:flex-1">
              <MapPanel
                :lat="data.member.lat"
                :lng="data.member.lng"
                height="h-[300px] lg:h-full"
                :zoom="15"
                single
              />
            </div>
            <div v-else class="mt-3 flex-1 text-sm text-(--ui-text-dimmed)">
              No location data.
            </div>
          </div>
        </div>

        <div class="grid gap-4 lg:grid-cols-2">
          <!-- System -->
          <div v-if="data.mqtt" class="rounded-lg border border-default bg-(--ui-bg) p-5 shadow-sm">
            <h2 class="text-sm font-medium text-(--ui-text-dimmed)">System</h2>
            <dl class="mt-3 grid grid-cols-2 gap-4 text-sm">
              <div>
                <dt class="text-(--ui-text-dimmed)">Hostname</dt>
                <dd class="mt-0.5 font-mono text-xs">{{ data.mqtt.hostname || "—" }}</dd>
              </div>
              <div>
                <dt class="text-(--ui-text-dimmed)">Model</dt>
                <dd class="mt-0.5 text-xs">{{ data.mqtt.model || "—" }}</dd>
              </div>
              <div>
                <dt class="text-(--ui-text-dimmed)">Board</dt>
                <dd class="mt-0.5 text-xs">{{ data.mqtt.board_name || "—" }}</dd>
              </div>
              <div>
                <dt class="text-(--ui-text-dimmed)">Firmware</dt>
                <dd class="mt-0.5 font-mono text-xs">{{ data.mqtt.release_version || "—" }}</dd>
              </div>
              <div>
                <dt class="text-(--ui-text-dimmed)">Target</dt>
                <dd class="mt-0.5 font-mono text-xs">{{ data.mqtt.release_target || "—" }}</dd>
              </div>
              <div>
                <dt class="text-(--ui-text-dimmed)">Serial</dt>
                <dd class="mt-0.5 font-mono text-xs">{{ data.mqtt.serialnumber || "—" }}</dd>
              </div>
              <div>
                <dt class="text-(--ui-text-dimmed)">Uptime</dt>
                <dd class="mt-0.5">{{ data.mqtt.uptime_string || fmtSeconds(data.mqtt.uptime || 0) || "—" }}</dd>
              </div>
            </dl>
            <div class="mt-4 space-y-1.5 border-t border-default pt-3 text-xs">
              <div class="flex items-center justify-between">
                <span class="text-(--ui-text-dimmed)">RCALL</span>
                <span :class="data.mqtt.is_rcall ? 'text-emerald-600' : 'text-(--ui-text-dimmed)'">{{ data.mqtt.is_rcall ? "running" : "off" }}</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-(--ui-text-dimmed)">WAF</span>
                <span :class="data.mqtt.is_waf ? 'text-emerald-600' : 'text-(--ui-text-dimmed)'">{{ data.mqtt.is_waf ? "enabled" : "off" }}</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-(--ui-text-dimmed)">Netify UUID</span>
                <span class="font-mono">{{ data.mqtt.netify_uuid || "—" }}</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-(--ui-text-dimmed)">Tailscale IP</span>
                <span class="font-mono">{{ data.mqtt.ipaddress_ts || "—" }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Quota -->
        <div class="rounded-lg border border-default bg-(--ui-bg) p-5 shadow-sm">
          <h2 class="text-sm font-medium text-(--ui-text-dimmed)">Quota</h2>
          <div v-if="data.mqtt" class="mt-3">
            <div class="mb-1 flex justify-between text-sm">
              <span class="text-(--ui-text)">{{ quotaPct }}% used</span>
              <span class="text-(--ui-text-dimmed)">
                {{ fmtBytes(data.mqtt.quota_first_current ?? 0) }} / {{ fmtBytes(data.mqtt.quota_first_total ?? 0) }}
              </span>
            </div>
            <div class="h-2 w-full overflow-hidden rounded-full bg-(--ui-bg-elevated)">
              <div
                :class="['h-full rounded-full', quotaPct > 90 ? 'bg-red-500' : quotaPct > 70 ? 'bg-amber-500' : 'bg-emerald-500']"
                :style="{ width: quotaPct + '%' }"
              />
            </div>
            <dl class="mt-4 grid grid-cols-2 gap-x-4 gap-y-2 text-sm md:grid-cols-4">
              <div>
                <dt class="text-(--ui-text-dimmed)">Used today</dt>
                <dd class="mt-0.5">{{ fmtBytes(data.mqtt.quota_first_day ?? 0) }}</dd>
              </div>
              <div>
                <dt class="text-(--ui-text-dimmed)">Yesterday</dt>
                <dd class="mt-0.5">{{ fmtBytes(data.mqtt.quota_prev ?? 0) }} / {{ fmtBytes(data.mqtt.quota_prev_total ?? 0) }}</dd>
              </div>
              <div>
                <dt class="text-(--ui-text-dimmed)">RX/TX (vnstat)</dt>
                <dd class="mt-0.5 font-mono text-xs">
                  {{ data.mqtt.rx_usage != null ? fmtBytes(data.mqtt.rx_usage) : "—" }} / {{ data.mqtt.tx_usage != null ? fmtBytes(data.mqtt.tx_usage) : "—" }}
                </dd>
              </div>
              <div>
                <dt class="text-(--ui-text-dimmed)">Total (vnstat)</dt>
                <dd class="mt-0.5 font-mono text-xs">{{ data.mqtt.total_usage != null ? fmtBytes(data.mqtt.total_usage) : "—" }}</dd>
              </div>
            </dl>
          </div>
          <div v-else class="mt-3 text-sm text-(--ui-text-dimmed)">No quota data.</div>
        </div>

        <!-- Telemetry -->
        <div class="rounded-lg border border-default bg-(--ui-bg) p-5 shadow-sm">
          <h2 class="text-sm font-medium text-(--ui-text-dimmed)">Telemetry</h2>
          <div v-if="data.mqtt">
            <div ref="chartEl" class="mt-3 h-64 w-full"></div>
            <div class="mt-2 flex flex-wrap gap-x-6 gap-y-1 text-xs text-(--ui-text-dimmed)">
              <span>CPU load: {{ data.mqtt.load_1 }} / {{ data.mqtt.load_5 }} / {{ data.mqtt.load_15 }}</span>
              <span>RSSI: {{ data.mqtt.rssi_signal ?? "—" }} dBm</span>
              <span>Last update: {{ data.mqtt.updated_at || "—" }}</span>
            </div>
          </div>
          <div v-else class="mt-3 text-sm text-(--ui-text-dimmed)">No telemetry for this member.</div>
        </div>

        <!-- Link status -->
        <div v-if="data.mqtt" class="rounded-lg border border-default bg-(--ui-bg) p-5 shadow-sm">
          <h2 class="text-sm font-medium text-(--ui-text-dimmed)">Link</h2>
          <dl class="mt-3 grid grid-cols-2 gap-4 text-sm md:grid-cols-4">
            <div>
              <dt class="text-(--ui-text-dimmed)">Packet loss</dt>
              <dd class="mt-0.5">
                <span :class="lossClass">{{ data.mqtt.packet_loss != null && data.mqtt.packet_loss >= 0 ? data.mqtt.packet_loss + "%" : "—" }}</span>
              </dd>
            </div>
            <div>
              <dt class="text-(--ui-text-dimmed)">RTT</dt>
              <dd class="mt-0.5">{{ data.mqtt.round_trip != null && data.mqtt.round_trip >= 0 ? data.mqtt.round_trip + " ms" : "—" }}</dd>
            </div>
            <div>
              <dt class="text-(--ui-text-dimmed)">Switch port up</dt>
              <dd class="mt-0.5 font-mono text-xs">{{ data.mqtt.switchport_up || "—" }}</dd>
            </div>
            <div>
              <dt class="text-(--ui-text-dimmed)">Port status</dt>
              <dd class="mt-0.5 font-mono text-xs">{{ data.mqtt.port_status || "—" }}</dd>
            </div>
          </dl>
        </div>

        <!-- Config -->
        <div v-if="data.member" class="rounded-lg border border-default bg-(--ui-bg) p-5 shadow-sm">
          <h2 class="text-sm font-medium text-(--ui-text-dimmed)">Configuration</h2>
          <dl class="mt-3 grid grid-cols-2 gap-4 text-sm md:grid-cols-4">
            <div>
              <dt class="text-(--ui-text-dimmed)">Authorized</dt>
              <dd class="mt-0.5">
                <span :class="data.member.is_authorized ? 'text-emerald-600' : 'text-red-600'">{{ data.member.is_authorized ? "yes" : "no" }}</span>
              </dd>
            </div>
            <div>
              <dt class="text-(--ui-text-dimmed)">Bridge</dt>
              <dd class="mt-0.5">{{ data.member.is_bridge ? "yes" : "no" }}</dd>
            </div>
            <div>
              <dt class="text-(--ui-text-dimmed)">No auto IP</dt>
              <dd class="mt-0.5">{{ data.member.is_no_auto_ip ? "yes" : "no" }}</dd>
            </div>
            <div>
              <dt class="text-(--ui-text-dimmed)">DPI</dt>
              <dd class="mt-0.5">{{ data.member.is_dpi ? "enabled" : "off" }}</dd>
            </div>
            <div>
              <dt class="text-(--ui-text-dimmed)">WAF</dt>
              <dd class="mt-0.5">{{ data.member.is_waf ? "enabled" : "off" }}</dd>
            </div>
            <div>
              <dt class="text-(--ui-text-dimmed)">Tags</dt>
              <dd class="mt-0.5 font-mono text-xs">{{ data.member.tags || "—" }}</dd>
            </div>
            <div>
              <dt class="text-(--ui-text-dimmed)">Mobile</dt>
              <dd class="mt-0.5 font-mono text-xs">{{ data.member.mobile_number_first || "—" }}</dd>
            </div>
            <div>
              <dt class="text-(--ui-text-dimmed)">Deauth timer</dt>
              <dd class="mt-0.5">{{ data.member.deauth_timer ? data.member.deauth_timer + " h" : "—" }}</dd>
            </div>
          </dl>
        </div>


        <!-- Problems -->
        <div v-if="data.problems.length" class="rounded-lg border border-default bg-(--ui-bg) p-5 shadow-sm">
          <h2 class="text-sm font-medium text-(--ui-text-dimmed)">Open problems</h2>
          <ul class="mt-3 space-y-2">
            <li
              v-for="(p, i) in data.problems"
              :key="i"
              class="flex items-center justify-between gap-2 rounded-lg border border-red-700/40 bg-red-500/10 px-3 py-2 text-sm"
            >
              <span class="text-red-600">{{ p.problem }}</span>
              <span class="shrink-0 text-xs text-(--ui-text-dimmed)">
                {{ p.start_at ? p.start_at.replace("T", " ").slice(0, 16) : "—" }}
                <template v-if="p.duration"> · {{ fmtSeconds(p.duration) }}</template>
              </span>
            </li>
          </ul>
        </div>
      </div>
      <div v-else class="p-4 text-sm text-(--ui-text-dimmed)">Loading…</div>

      <UModal v-model:open="modalOpen" title="Edit Member">
        <template #body>
          <UForm :state="form" @submit="submit">
            <UFormField label="Name" name="name" required>
              <UInput v-model="form.name" />
            </UFormField>
            <UFormField label="Member Code" name="member_code">
              <UInput v-model="form.member_code" />
            </UFormField>
            <UFormField label="IP Address" name="ipaddress">
              <UInput v-model="form.ipaddress" placeholder="Comma-separated; must be inside the network CIDR" />
            </UFormField>
            <UFormField label="Tags" name="tags">
              <UInput v-model="form.tags" />
            </UFormField>
            <UFormField label="Description" name="description">
              <UTextarea v-model="form.description" />
            </UFormField>
            <div class="mt-2 grid gap-2">
              <UCheckbox v-model="form.is_authorized" label="Authorized" />
              <UCheckbox v-model="form.is_bridge" label="Bridge mode" />
              <UCheckbox v-model="form.is_no_auto_ip" label="No auto assign IP" />
            </div>
            <p class="mt-2 text-xs text-(--ui-text-dimmed)">
              Member ID and network are immutable; re-adopt on another network instead.
            </p>
            <div v-if="error" class="mt-2 p-2 rounded bg-red-50 text-red-700 text-sm dark:bg-red-900/20 dark:text-red-400">{{ error }}</div>
            <div class="flex justify-end gap-2 pt-4">
              <UButton variant="outline" @click="modalOpen = false">Cancel</UButton>
              <UButton type="submit" :loading="saving">Save</UButton>
            </div>
          </UForm>
        </template>
      </UModal>
    </template>
  </UDashboardPanel>
</template>

<script setup lang="ts">
import type { TelemetryResponse } from "~/types/api";

const data = ref<TelemetryResponse | null>(null);
const route = useRoute();
const auth = useAuthStore();
await requireAuth();
if (auth.loggedIn) {
  try {
    data.value = await api<TelemetryResponse>(
      `/api/app/members/${encodeURIComponent(route.params.memberId as string)}/telemetry/`,
    );
  } catch {
    data.value = null;
  }
}

// Capability from the server (§C); the write views re-check regardless.
const canChange = computed(() => auth.me?.permissions?.members_change === true);
const canDelete = computed(() => auth.me?.permissions?.members_delete === true);

const modalOpen = ref(false);
const saving = ref(false);
const error = ref("");
const form = reactive({
  name: "",
  member_code: "",
  description: "",
  ipaddress: "",
  tags: "",
  is_authorized: false,
  is_bridge: false,
  is_no_auto_ip: false,
});

async function openEdit() {
  if (!data.value) return;
  error.value = "";
  // The list/telemetry payload is informational; the edit form loads the row
  // itself so a stale page can never PATCH over a newer value (§C).
  const row = await fetchMemberDetail(data.value.member.member_id);
  form.name = row.name;
  form.member_code = row.member_code || "";
  form.description = row.description || "";
  form.ipaddress = row.ipaddress || "";
  form.tags = row.tags || "";
  form.is_authorized = !!row.is_authorized;
  form.is_bridge = row.is_bridge;
  form.is_no_auto_ip = row.is_no_auto_ip;
  modalOpen.value = true;
}

function ruleMessage(data: any): string {
  const rule = data?.rule;
  if (rule === "superuser_no_member_write") {
    return "A superuser cannot write members (platform operator, not tenant).";
  }
  if (rule && rule !== "perm_missing") return `Denied: ${rule}`;
  if (typeof data?.error === "string") return data.error;
  if (data?.error) return JSON.stringify(data.error);
  return "Request failed";
}

async function submit() {
  if (!data.value) return;
  saving.value = true;
  error.value = "";
  try {
    const row = await updateMember(data.value.member.member_id, { ...form });
    modalOpen.value = false;
    data.value.member.name = row.name;
    data.value.member.member_code = row.member_code;
    data.value.member.description = row.description;
    data.value.member.ipaddress = row.ipaddress;
    data.value.member.tags = row.tags;
    data.value.member.is_authorized = row.is_authorized;
    data.value.member.is_bridge = row.is_bridge;
    data.value.member.is_no_auto_ip = row.is_no_auto_ip;
  } catch (e: any) {
    error.value = ruleMessage(e?.data || e);
  } finally {
    saving.value = false;
  }
}

async function remove() {
  if (!data.value) return;
  const id = data.value.member.member_id;
  if (!confirm(`Delete member "${data.value.member.name}"? This removes it from the controller too.`)) {
    return;
  }
  try {
    await deleteMember(id);
  } catch (e: any) {
    const body = e?.data;
    if (body?.rule === "controller_refused_delete") {
      // §V42: the controller no longer has this member, so the row can only be
      // dropped locally — and only after the caller sees the refusal.
      const refusal = typeof body.error === "string" ? body.error : "controller refused delete";
      if (!confirm(`${refusal}\n\nDrop the local row anyway (leaves the controller alone)?`)) {
        return;
      }
      await deleteMember(id, true);
    } else {
      alert(ruleMessage(body || e));
      return;
    }
  }
  navigateTo("/members");
}

const chartEl = ref<HTMLElement | null>(null);
const { setOption, dispose } = useECharts(chartEl);

function fmtSeconds(s: number): string {
  if (s < 60) return `${s}s`;
  if (s < 3600) return `${Math.round(s / 60)}m`;
  if (s < 86400) return `${Math.round(s / 3600)}h`;
  return `${Math.round(s / 86400)}d`;
}

function fmtBytes(n: number): string {
  const units = ["B", "KB", "MB", "GB", "TB"];
  let v = n;
  let u = 0;
  while (v >= 1024 && u < units.length - 1) {
    v /= 1024;
    u++;
  }
  return `${v.toFixed(v >= 100 || u === 0 ? 0 : 1)} ${units[u]}`;
}

const onlineLabel = computed(() =>
  data.value?.member.is_online ? "Online" : "Offline",
);
const displayIp = computed(
  () => data.value?.mqtt?.ipaddress || data.value?.member.ipaddress || "—",
);
const quotaPct = computed(() => {
  const m = data.value?.mqtt;
  if (!m || !m.quota_first_total) return 0;
  const cur = m.quota_first_current ?? 0;
  return Math.min(100, Math.round((cur / m.quota_first_total) * 100));
});
const lossClass = computed(() => {
  const loss = data.value?.mqtt?.packet_loss;
  if (loss == null || loss < 0) return "";
  return loss > 5 ? "text-red-600" : loss > 1 ? "text-amber-600" : "text-emerald-600";
});

// Data is loaded during setup (top-level await), so the template is already
// rendered by onMounted — a watcher would fire before chartEl exists.
onMounted(async () => {
  await nextTick();
  const m = data.value?.mqtt;
  if (!m || !chartEl.value) return;
  setOption({
    tooltip: {},
    xAxis: { type: "category", data: ["CPU", "Mem", "Loss", "RTT", "Load"] },
    yAxis: { type: "value" },
    series: [
      {
        type: "bar",
        data: [
          m.cpu_usage ?? 0,
          m.memory_usage ?? 0,
          m.packet_loss != null && m.packet_loss >= 0 ? m.packet_loss : 0,
          m.round_trip != null && m.round_trip >= 0 ? m.round_trip : 0,
          m.load_1 ?? 0,
        ],
        itemStyle: { color: "#0ea5e9" },
      },
    ],
  });
});

onUnmounted(dispose);
</script>