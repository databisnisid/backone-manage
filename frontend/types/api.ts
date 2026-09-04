// API types — mirror app/views.py response shapes (prepare_data + enrichment)

export interface MeResponse {
  user: { id: number; username: string; name_or_email: string };
  organization: {
    uuid: string | null;
    name: string | null;
    is_no_org: boolean | null;
  };
  is_superuser: boolean;
  features: { is_2fa: boolean; is_mailauth_no_password: boolean };
}

export interface Member {
  id: number;
  name: string;
  member_id: string;
  address: string | null;
  ipaddress: string | null;
  lat: number | null;
  lng: number | null;
  is_online: number;
  is_problem: number;
  problem_string: string;
  is_new: number;
  is_authorized: number;
  network_id: string;
  organization: string | null;
  mqtt?: MqttSummary | null;
}

export interface MqttSummary {
  cpu_usage: number | null;
  memory_usage: number | null;
  packet_loss: number | null;
  round_trip: number | null;
  uptime: number | null;
  rssi_signal: number | null;
  updated_at: string | null;
}

export interface MemberProblemInfo {
  problem: string | null;
  start_at: string | null;
  duration: number | null;
}

export interface MemberDetailInfo {
  member_id: string;
  name: string;
  member_code: string | null;
  description: string | null;
  address: string | null;
  location: string | null;
  ipaddress: string | null;
  is_online: number;
  is_authorized: number;
  is_bridge: boolean;
  is_no_auto_ip: boolean;
  is_dpi: boolean;
  is_waf: boolean;
  tags: string | null;
  mobile_number_first: string | null;
  online_at: string | null;
  offline_at: string | null;
  deauth_timer: number;
  deauth_timer_start: string | null;
  created_at: string | null;
  updated_at: string | null;
  organization: string | null;
  network: { network_id: string; name: string } | null;
  is_problem: number;
  lat: number | null;
  lng: number | null;
}

export interface TelemetryResponse {
  member: MemberDetailInfo;
  problems: MemberProblemInfo[];
  mqtt: MqttDetail | null;
}

export interface MqttDetail extends MqttSummary {
  num_core: number;
  hostname: string | null;
  model: string | null;
  board_name: string | null;
  release_version: string | null;
  release_target: string | null;
  serialnumber: string | null;
  switchport_up: string | null;
  port_status: string | null;
  ipaddress_ts: string | null;
  is_rcall: boolean;
  is_waf: boolean;
  netify_uuid: string | null;
  quota_first: string | null;
  quota_first_raw: string | null;
  quota_first_current: number | null;
  quota_first_total: number | null;
  quota_first_day: number | null;
  quota_type: string | null;
  quota_prev: number | null;
  quota_prev_total: number | null;
  quota_prev_day: number | null;
  quota_prev_raw: string | null;
  quota_vnstat: string | null;
  rx_usage: number | null;
  tx_usage: number | null;
  total_usage: number | null;
  load_1: number | null;
  load_5: number | null;
  load_15: number | null;
  uptime_string: string | null;
  ipaddress: string | null;
  created_at: string | null;
  is_online: number;
}

export interface Network {
  network_id: string;
  name: string;
  description: string;
  member_count: number;
}

export interface Summary {
  members: number;
  online: number;
  problems: number;
  networks: number;
}

export interface Problem {
  member: { member_id: string; name: string };
  problem: string | null;
  start_at: string | null;
  duration: number | null;
  is_done: boolean;
  network: string | null;
}