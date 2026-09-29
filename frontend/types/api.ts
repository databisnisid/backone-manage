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
  ip_allocation: string;
  member_count: number;
  route_count: number;
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

export interface Route {
  id: number;
  ip_network: string;
  gateway: string | null;
  gateway_member_name: string | null;
  network_id: string;
  created_at: string | null;
  updated_at: string | null;
}

export interface NetworkDetail {
  network_id: string;
  name: string;
  description: string;
  ip_allocation: string;
  member_count: number;
  controller_name: string | null;
}


export interface Controller {
  id: number;
  name: string;
  description: string;
  uri: string;
  token: string;
}

export interface Feature {
  id: number;
  name: string;
  is_2fa: boolean;
  is_mailauth_no_password: boolean;
  is_webfilter: boolean;
  is_webfilter_multinet: boolean;
  is_headscale: boolean;
  is_zabbix: boolean;
}

export interface LicenseItem {
  id: number;
  node_id: string;
  organization_uuid: string | null;
  is_block_rule: boolean;
  license_string: string;
  license_features: string;
  created_at: string | null;
}

export interface WebFilter {
  id: number;
  name: string;
  domains_black: string;
  domains_white: string;
  is_default_block: boolean;
  organization_uuid: string | null;
}

export interface WebFilterOrg {
  id: number;
  webfilter_id: number;
  webfilter_name: string;
  network_id: string;
  network_name: string;
  organization_uuid: string | null;
}

export interface WebFilterMember {
  id: number;
  webfilter_id: number;
  member_id: number;
  member_name: string;
  member_member_id: string;
}

export interface ZabbixConfig {
  id: number;
  name: string;
  url: string;
  token: string;
}

export interface MonitorRule {
  id: number;
  name: string;
  item_id: number;
  item_name: string;
  threshold_min: number;
  threshold_max: number;
  duration: number;
  organization_uuid: string | null;
}

export interface MonitorItem {
  id: number;
  name: string;
  item_id: number;
}

export interface HSUser {
  id: number;
  name: string;
  description: string;
  created_at: string | null;
}

export interface HSNode {
  id: number;
  name: string;
  machine_key: string;
  node_key: string;
  addresses: string;
  created_at: string | null;
}

export interface HSPreauthkey {
  id: number;
  key: string;
  is_reusable: boolean;
  is_ephemeral: boolean;
  is_used: boolean;
  hs_user_id: number;
  expiration: string | null;
  created_at: string | null;
}

export interface OperationalTime {
  id: number;
  network_id: string;
  network_name: string | null;
  is_mon: boolean;
  is_tue: boolean;
  is_wed: boolean;
  is_thu: boolean;
  is_fri: boolean;
  is_sat: boolean;
  is_sun: boolean;
  mon_start: number;
  mon_end: number;
  tue_start: number;
  tue_end: number;
  wed_start: number;
  wed_end: number;
  thu_start: number;
  thu_end: number;
  fri_start: number;
  fri_end: number;
  sat_start: number;
  sat_end: number;
  sun_start: number;
  sun_end: number;
  created_at: string | null;
  updated_at: string | null;
}

export interface Feature {
  id: number;
  name: string;
  description: string;
  uuid: string;
  number_of_network: number;
  number_of_member: number;
  network_multi_ip: boolean;
  network_rules: boolean;
  member_multi_ip: boolean;
  authorize: boolean;
  bridge: boolean;
  tags: boolean;
  web: boolean;
  ssh: boolean;
  synchronize: boolean;
  geolocation: boolean;
  online_offline: boolean;
  is_export: boolean;
  mobile_connect: boolean;
  map_dashboard: boolean;
  is_nms: boolean;
  is_webfilter: boolean;
  is_webfilter_multinet: boolean;
  is_dpi: boolean;
  is_telkomsel: boolean;
  is_deauth_timer: boolean;
  is_simple_list: boolean;
  is_lte_signal: boolean;
  created_at: string | null;
  updated_at: string | null;
}

export interface DeviceItem {
  id: number;
  name: string;
  device_id: string;
  username: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface OrgWithDevices {
  id: number;
  name: string;
  uuid: string;
  devices: DeviceItem[];
}