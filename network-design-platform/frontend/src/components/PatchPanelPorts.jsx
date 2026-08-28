import { useEffect, useState } from "react";
import { api } from "../api/client";

/**
 * Port grid for a patch panel -- click a port to label it and mark it
 * patched/reserved. This is Phase 1's stand-in for what Phase 2 wires up
 * for real (assigning a cable drop to a port, replacing the
 * 'TransposeValuesOnly' macro's 24-row copy/paste/transpose).
 */
export function PatchPanelPorts({ panelId, panelName }) {
  const [panel, setPanel] = useState(null);
  const [editingPortId, setEditingPortId] = useState(null);
  const [draft, setDraft] = useState({ label: "", status: "free" });

  const refresh = () => api.getPatchPanel(panelId).then(setPanel);
  useEffect(() => {
    refresh();
    setEditingPortId(null);
  }, [panelId]);

  if (!panel) return null;

  const startEdit = (port) => {
    setEditingPortId(port.id);
    setDraft({ label: port.label || "", status: port.status });
  };

  const save = async (e) => {
    e.preventDefault();
    await api.updatePort(panelId, editingPortId, draft);
    setEditingPortId(null);
    refresh();
  };

  return (
    <div className="patch-panel-ports">
      <h5>{panelName} — {panel.port_count} ports</h5>
      <div className="port-grid">
        {panel.ports.map((port) => (
          <button
            key={port.id}
            type="button"
            className={`port port--${port.status}${editingPortId === port.id ? " port--editing" : ""}`}
            title={port.label || `Port ${port.port_number}`}
            onClick={() => startEdit(port)}
          >
            {port.port_number}
          </button>
        ))}
      </div>

      {editingPortId && (
        <form className="inline-form port-edit-form" onSubmit={save}>
          <span>Port {panel.ports.find((p) => p.id === editingPortId)?.port_number}</span>
          <input
            placeholder="Label (e.g. Room 101 - Drop 3)"
            value={draft.label}
            onChange={(e) => setDraft((d) => ({ ...d, label: e.target.value }))}
          />
          <select
            value={draft.status}
            onChange={(e) => setDraft((d) => ({ ...d, status: e.target.value }))}
          >
            <option value="free">Free</option>
            <option value="patched">Patched</option>
            <option value="reserved">Reserved</option>
          </select>
          <button type="submit">Save</button>
        </form>
      )}
    </div>
  );
}
