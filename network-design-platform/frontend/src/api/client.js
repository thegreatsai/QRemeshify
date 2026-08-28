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

  getReferenceList: (key) => request(`/reference-lists/${key}`),
};
