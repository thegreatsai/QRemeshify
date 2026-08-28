const BASE_URL = "/api";

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request to ${path} failed with ${res.status}`);
  }
  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  listSites: () => request("/sites"),
  createSite: (payload) => request("/sites", { method: "POST", body: JSON.stringify(payload) }),
  updateSite: (id, payload) =>
    request(`/sites/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),

  listRooms: (siteId) => request(`/sites/${siteId}/rooms`),
  createRoom: (siteId, payload) =>
    request(`/sites/${siteId}/rooms`, { method: "POST", body: JSON.stringify(payload) }),

  listRacks: (siteId) => request(`/sites/${siteId}/racks`),
  createRack: (siteId, payload) =>
    request(`/sites/${siteId}/racks`, { method: "POST", body: JSON.stringify(payload) }),

  listRackItems: (rackId) => request(`/racks/${rackId}/items`),
  createRackItem: (rackId, payload) =>
    request(`/racks/${rackId}/items`, { method: "POST", body: JSON.stringify(payload) }),
  moveRackItem: (rackId, itemId, startU) =>
    request(`/racks/${rackId}/items/${itemId}/move`, {
      method: "PATCH",
      body: JSON.stringify({ start_u: startU }),
    }),
  deleteRackItem: (rackId, itemId) =>
    request(`/racks/${rackId}/items/${itemId}`, { method: "DELETE" }),

  createPatchPanel: (rackId, itemId, portCount) =>
    request(`/racks/${rackId}/items/${itemId}/patch-panel`, {
      method: "POST",
      body: JSON.stringify({ port_count: portCount }),
    }),
  getPatchPanel: (panelId) => request(`/patch-panels/${panelId}`),
  updatePort: (panelId, portId, payload) =>
    request(`/patch-panels/${panelId}/ports/${portId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),

  listCableDrops: (siteId) => request(`/sites/${siteId}/cable-drops`),
  createCableDrop: (siteId, payload) =>
    request(`/sites/${siteId}/cable-drops`, { method: "POST", body: JSON.stringify(payload) }),
  updateCableDrop: (dropId, payload) =>
    request(`/cable-drops/${dropId}`, { method: "PATCH", body: JSON.stringify(payload) }),
  deleteCableDrop: (dropId) => request(`/cable-drops/${dropId}`, { method: "DELETE" }),
  assignCableDrop: (dropId, portId) =>
    request(`/cable-drops/${dropId}/assign`, { method: "POST", body: JSON.stringify({ port_id: portId }) }),
  unassignCableDrop: (dropId) => request(`/cable-drops/${dropId}/unassign`, { method: "POST" }),
  bulkImportCableDrops: (siteId, rows) =>
    request(`/sites/${siteId}/cable-drops/bulk`, { method: "POST", body: JSON.stringify({ rows }) }),

  listSitePorts: (siteId, freeOnly = false) =>
    request(`/sites/${siteId}/ports${freeOnly ? "?free_only=true" : ""}`),

  createSwitch: (rackId, itemId, model, portCount, managementIp) =>
    request(`/racks/${rackId}/items/${itemId}/switch`, {
      method: "POST",
      body: JSON.stringify({ model, port_count: portCount, management_ip: managementIp || null }),
    }),
  getSwitch: (switchId) => request(`/switches/${switchId}`),
  updateSwitchPort: (switchId, portId, payload) =>
    request(`/switches/${switchId}/ports/${portId}`, { method: "PATCH", body: JSON.stringify(payload) }),
  switchExportUrl: (switchId, interfacePrefix) =>
    `${BASE_URL}/switches/${switchId}/export${interfacePrefix ? `?interface_prefix=${encodeURIComponent(interfacePrefix)}` : ""}`,

  listVlans: (siteId) => request(`/sites/${siteId}/vlans`),
  createVlan: (siteId, payload) =>
    request(`/sites/${siteId}/vlans`, { method: "POST", body: JSON.stringify(payload) }),
  deleteVlan: (vlanId) => request(`/vlans/${vlanId}`, { method: "DELETE" }),

  assignCableDropSwitchPort: (dropId, switchPortId) =>
    request(`/cable-drops/${dropId}/assign-switch-port`, {
      method: "POST",
      body: JSON.stringify({ switch_port_id: switchPortId }),
    }),
  unassignCableDropSwitchPort: (dropId) =>
    request(`/cable-drops/${dropId}/unassign-switch-port`, { method: "POST" }),
  listSiteSwitchPorts: (siteId, freeOnly = false) =>
    request(`/sites/${siteId}/switch-ports${freeOnly ? "?free_only=true" : ""}`),

  calculatePortAllocation: (payload) =>
    request(`/port-allocation/calculate`, { method: "POST", body: JSON.stringify(payload) }),

  getReferenceList: (key) => request(`/reference-lists/${key}`),
};
