import { useEffect, useState } from "react";
import { api } from "../api/client";
import { PatchPanelPorts } from "./PatchPanelPorts";
import { ReferenceSelect } from "./ReferenceSelect";

const SLOT_HEIGHT = 28; // px per rack U

/**
 * The direct replacement for the old 'Rack Elevations' sheet's merged-cell
 * blocks: a U-slot grid (U1 at the bottom, matching real elevation
 * convention) where equipment is dragged to reposition it. Every move is
 * validated server-side against overlap with other equipment and the
 * rack's total_u capacity (see app/routers/rack_items.py), so a rejected
 * drop shows an error instead of silently corrupting the layout.
 */
export function RackElevation({ rack, refreshSignal, onChange }) {
  const [items, setItems] = useState([]);
  const [error, setError] = useState(null);
  const [expandedItemId, setExpandedItemId] = useState(null);
  const [dragOverU, setDragOverU] = useState(null);
  const [form, setForm] = useState({ name: "", equipment_type: "", start_u: "1", size_u: "1" });

  const refresh = () => api.listRackItems(rack.id).then(setItems);

  useEffect(() => {
    refresh();
    setExpandedItemId(null);
    setError(null);
  }, [rack.id]);

  // A shared-refresh tick (e.g. a drop assignment made from the Drop List)
  // should just re-fetch this rack's items -- not collapse whichever
  // patch panel the user has open.
  useEffect(() => {
    if (refreshSignal !== undefined) refresh();
  }, [refreshSignal]);

  const itemAt = (u) => items.find((i) => u >= i.start_u && u <= i.start_u + i.size_u - 1);
  const isTopOfItem = (item, u) => item.start_u + item.size_u - 1 === u;

  const addItem = async (e) => {
    e.preventDefault();
    setError(null);
    try {
      await api.createRackItem(rack.id, {
        name: form.name,
        equipment_type: form.equipment_type,
        start_u: Number(form.start_u),
        size_u: Number(form.size_u),
      });
      setForm({ name: "", equipment_type: "", start_u: "1", size_u: "1" });
      refresh();
      onChange();
    } catch (err) {
      setError(err.message);
    }
  };

  const dropOn = async (targetU, e) => {
    e.preventDefault();
    setDragOverU(null);
    const itemId = Number(e.dataTransfer.getData("text/plain"));
    if (!itemId) return;
    setError(null);
    try {
      await api.moveRackItem(rack.id, itemId, targetU);
      refresh();
      onChange();
    } catch (err) {
      setError(err.message);
    }
  };

  const deleteItem = async (itemId, ev) => {
    ev.stopPropagation();
    await api.deleteRackItem(rack.id, itemId);
    if (expandedItemId === itemId) setExpandedItemId(null);
    refresh();
    onChange();
  };

  const addPorts = async (itemId, ev) => {
    ev.stopPropagation();
    const count = window.prompt("Number of ports on this patch panel?", "24");
    if (!count) return;
    setError(null);
    try {
      await api.createPatchPanel(rack.id, itemId, Number(count));
      refresh();
      setExpandedItemId(itemId);
      onChange();
    } catch (err) {
      setError(err.message);
    }
  };

  const rows = [];
  for (let u = rack.total_u; u >= 1; u--) {
    const item = itemAt(u);
    if (item && !isTopOfItem(item, u)) continue; // rendered as part of its top row

    if (!item) {
      rows.push(
        <div
          key={u}
          className={`rack-slot${dragOverU === u ? " rack-slot--drag-over" : ""}`}
          style={{ height: SLOT_HEIGHT }}
          onDragOver={(e) => {
            e.preventDefault();
            setDragOverU(u);
          }}
          onDragLeave={() => setDragOverU((cur) => (cur === u ? null : cur))}
          onDrop={(e) => dropOn(u, e)}
        >
          <span className="rack-slot-label">U{u}</span>
        </div>
      );
      continue;
    }

    rows.push(
      <div
        key={u}
        className={`rack-slot rack-slot--filled`}
        style={{ height: item.size_u * SLOT_HEIGHT }}
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => dropOn(item.start_u, e)}
      >
        <span className="rack-slot-label">U{u}</span>
        <div
          className={`rack-item rack-item--${item.equipment_type}`}
          draggable
          onDragStart={(e) => e.dataTransfer.setData("text/plain", String(item.id))}
          onClick={() => item.patch_panel && setExpandedItemId(expandedItemId === item.id ? null : item.id)}
        >
          <span className="rack-item-name">
            {item.name} <span className="tag">{item.equipment_type}</span>
          </span>
          <span className="rack-item-actions">
            {item.equipment_type === "patch_panel" && !item.patch_panel && (
              <button type="button" onClick={(e) => addPorts(item.id, e)}>
                Add Ports
              </button>
            )}
            <button type="button" className="rack-item-delete" onClick={(e) => deleteItem(item.id, e)}>
              ×
            </button>
          </span>
        </div>
      </div>
    );
  }

  const expandedItem = items.find((i) => i.id === expandedItemId);

  return (
    <div className="rack-elevation">
      <h4>
        {rack.rack_number} <span className="tag">{rack.total_u}U</span>
      </h4>
      {error && <p className="form-error">{error}</p>}
      <div className="rack-grid">{rows}</div>

      <form className="inline-form rack-add-form" onSubmit={addItem}>
        <input
          placeholder="Equipment name"
          value={form.name}
          onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
        />
        <ReferenceSelect
          listKey="rack_equipment_type"
          value={form.equipment_type}
          onChange={(v) => setForm((f) => ({ ...f, equipment_type: v }))}
        />
        <input
          type="number"
          min="1"
          max={rack.total_u}
          title="Start U"
          value={form.start_u}
          onChange={(e) => setForm((f) => ({ ...f, start_u: e.target.value }))}
        />
        <input
          type="number"
          min="1"
          max={rack.total_u}
          title="Size (U)"
          value={form.size_u}
          onChange={(e) => setForm((f) => ({ ...f, size_u: e.target.value }))}
        />
        <button type="submit">Add Equipment</button>
      </form>

      {expandedItem?.patch_panel && (
        <PatchPanelPorts
          siteId={rack.site_id}
          panelId={expandedItem.patch_panel.id}
          panelName={expandedItem.name}
          refreshSignal={refreshSignal}
          onChange={onChange}
        />
      )}
    </div>
  );
}
