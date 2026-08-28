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

  getReferenceList: (key) => request(`/reference-lists/${key}`),
};
