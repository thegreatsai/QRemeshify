import { useEffect, useState } from "react";
import { api } from "../api/client";

/** Replaces the VLAN identity implied by 'VLAN Config (9300)'/'(2960)' and
 * the tallies on 'VLAN Counts' -- a real per-site VLAN registry that
 * switch ports reference by id instead of a hand-typed number. */
export function VlanManager({ site, refreshSignal, onChange }) {
  const [vlans, setVlans] = useState([]);
  const [error, setError] = useState(null);
  const [form, setForm] = useState({ vlan_number: "", name: "", purpose: "" });

  const refresh = () => {
    api.listVlans(site.id).then(setVlans);
  };
  useEffect(refresh, [site.id, refreshSignal]);

  const addVlan = async (e) => {
    e.preventDefault();
    if (!form.vlan_number || !form.name) return;
    setError(null);
    try {
      await api.createVlan(site.id, {
        vlan_number: Number(form.vlan_number),
        name: form.name,
        purpose: form.purpose || null,
      });
      setForm({ vlan_number: "", name: "", purpose: "" });
      refresh();
      onChange();
    } catch (err) {
      setError(err.message);
    }
  };

  const removeVlan = async (vlanId) => {
    setError(null);
    try {
      await api.deleteVlan(vlanId);
      refresh();
      onChange();
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="vlan-manager">
      {error && <p className="form-error">{error}</p>}
      <table className="drop-table">
        <thead>
          <tr>
            <th>VLAN</th>
            <th>Name</th>
            <th>Purpose</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {vlans.map((v) => (
            <tr key={v.id}>
              <td>{v.vlan_number}</td>
              <td>{v.name}</td>
              <td>{v.purpose || "—"}</td>
              <td>
                <button type="button" className="rack-item-delete" onClick={() => removeVlan(v.id)}>
                  ×
                </button>
              </td>
            </tr>
          ))}
          {vlans.length === 0 && (
            <tr>
              <td colSpan={4} className="empty-state">
                No VLANs defined yet.
              </td>
            </tr>
          )}
        </tbody>
      </table>
      <form className="inline-form" onSubmit={addVlan}>
        <input
          type="number"
          placeholder="VLAN #"
          value={form.vlan_number}
          onChange={(e) => setForm((f) => ({ ...f, vlan_number: e.target.value }))}
        />
        <input
          placeholder="Name"
          value={form.name}
          onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
        />
        <input
          placeholder="Purpose (optional)"
          value={form.purpose}
          onChange={(e) => setForm((f) => ({ ...f, purpose: e.target.value }))}
        />
        <button type="submit">Add VLAN</button>
      </form>
    </div>
  );
}
