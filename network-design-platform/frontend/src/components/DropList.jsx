import { useEffect, useState } from "react";
import { api } from "../api/client";

/**
 * Replaces 'Drop List Draft' / 'Drop List As-Built'. Every row's port
 * assignment is read straight from CableDrop.port_id -- the same field the
 * Patch Panel port grid reads -- so assigning or moving a drop here (or
 * over there) shows up on both without a manual sync/transpose step.
 */
export function DropList({ site, rooms, refreshSignal, onChange }) {
  const [drops, setDrops] = useState([]);
  const [ports, setPorts] = useState([]);
  const [error, setError] = useState(null);
  const [form, setForm] = useState({ drop_number: "", room_id: "", vlan: "", voice_vlan: "" });
  const [bulkText, setBulkText] = useState("");
  const [bulkResult, setBulkResult] = useState(null);
  const [showBulk, setShowBulk] = useState(false);

  const refresh = () => {
    api.listCableDrops(site.id).then(setDrops);
    api.listSitePorts(site.id).then(setPorts);
  };

  useEffect(refresh, [site.id, refreshSignal]);

  const roomName = (roomId) => rooms.find((r) => r.id === roomId)?.name;

  const addDrop = async (e) => {
    e.preventDefault();
    if (!form.drop_number) return;
    setError(null);
    try {
      await api.createCableDrop(site.id, {
        drop_number: form.drop_number,
        room_id: form.room_id ? Number(form.room_id) : null,
        vlan: form.vlan || null,
        voice_vlan: form.voice_vlan || null,
      });
      setForm({ drop_number: "", room_id: "", vlan: "", voice_vlan: "" });
      refresh();
      onChange();
    } catch (err) {
      setError(err.message);
    }
  };

  /**
   * Expects lines of `drop_number,room_name,vlan,voice_vlan` (room/vlan/
   * voice_vlan optional, trailing commas can be omitted). Upserts by drop
   * number, so re-pasting a revised list updates existing rows instead of
   * erroring on duplicates.
   */
  const runBulkImport = async (e) => {
    e.preventDefault();
    const rows = bulkText
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean)
      .map((line) => {
        const [drop_number, room_name, vlan, voice_vlan] = line.split(",").map((s) => s.trim());
        return {
          drop_number,
          room_name: room_name || null,
          vlan: vlan || null,
          voice_vlan: voice_vlan || null,
        };
      });
    if (rows.length === 0) return;
    setError(null);
    try {
      const result = await api.bulkImportCableDrops(site.id, rows);
      setBulkResult(result);
      setBulkText("");
      refresh();
      onChange();
    } catch (err) {
      setError(err.message);
    }
  };

  const deleteDrop = async (dropId) => {
    await api.deleteCableDrop(dropId);
    refresh();
    onChange();
  };

  const assignTo = async (drop, portId) => {
    setError(null);
    try {
      if (portId === "") {
        await api.unassignCableDrop(drop.id);
      } else {
        await api.assignCableDrop(drop.id, Number(portId));
      }
      refresh();
      onChange(); // instantly refetches the Patch Panel view too
    } catch (err) {
      setError(err.message);
    }
  };

  const portOptions = (drop) => {
    const currentPortId = drop.port_location?.port_id;
    return ports.map((p) => {
      const occupiedByOther = p.cable_drop_id != null && p.cable_drop_id !== drop.id;
      return { ...p, disabled: occupiedByOther };
    });
  };

  return (
    <div className="drop-list">
      {error && <p className="form-error">{error}</p>}
      <table className="drop-table">
        <thead>
          <tr>
            <th>Drop #</th>
            <th>Room</th>
            <th>VLAN</th>
            <th>Voice VLAN</th>
            <th>Status</th>
            <th>Patched At</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {drops.map((drop) => (
            <tr key={drop.id}>
              <td>{drop.drop_number}</td>
              <td>{roomName(drop.room_id) || "—"}</td>
              <td>{drop.vlan || "—"}</td>
              <td>{drop.voice_vlan || "—"}</td>
              <td>
                <span className={`tag tag--${drop.status}`}>{drop.status}</span>
              </td>
              <td>
                <select
                  className="reference-select"
                  value={drop.port_location?.port_id ?? ""}
                  onChange={(e) => assignTo(drop, e.target.value)}
                >
                  <option value="">Unassigned</option>
                  {portOptions(drop).map((p) => (
                    <option key={p.port_id} value={p.port_id} disabled={p.disabled}>
                      {p.rack_number} / {p.rack_item_name} / Port {p.port_number}
                      {p.disabled ? " (occupied)" : ""}
                    </option>
                  ))}
                </select>
              </td>
              <td>
                <button type="button" className="rack-item-delete" onClick={() => deleteDrop(drop.id)}>
                  ×
                </button>
              </td>
            </tr>
          ))}
          {drops.length === 0 && (
            <tr>
              <td colSpan={7} className="empty-state">
                No drops yet.
              </td>
            </tr>
          )}
        </tbody>
      </table>

      <form className="inline-form" onSubmit={addDrop}>
        <input
          placeholder="Drop number (e.g. D001)"
          value={form.drop_number}
          onChange={(e) => setForm((f) => ({ ...f, drop_number: e.target.value }))}
        />
        <select
          className="reference-select"
          value={form.room_id}
          onChange={(e) => setForm((f) => ({ ...f, room_id: e.target.value }))}
        >
          <option value="">No room</option>
          {rooms.map((room) => (
            <option key={room.id} value={room.id}>
              {room.name}
            </option>
          ))}
        </select>
        <input
          placeholder="VLAN"
          value={form.vlan}
          onChange={(e) => setForm((f) => ({ ...f, vlan: e.target.value }))}
        />
        <input
          placeholder="Voice VLAN"
          value={form.voice_vlan}
          onChange={(e) => setForm((f) => ({ ...f, voice_vlan: e.target.value }))}
        />
        <button type="submit">Add Drop</button>
      </form>

      <button type="button" className="bulk-import-toggle" onClick={() => setShowBulk((s) => !s)}>
        {showBulk ? "Hide bulk import" : "Bulk import..."}
      </button>

      {showBulk && (
        <form className="bulk-import-form" onSubmit={runBulkImport}>
          <p className="bulk-import-hint">
            One drop per line: <code>drop_number, room name, vlan, voice vlan</code> (room/vlan/voice
            vlan optional). Re-pasting an existing drop number updates that row.
          </p>
          <textarea
            rows={6}
            placeholder={"D001, Room 101, VLAN 10, VLAN 110\nD002, Room 102, VLAN 10"}
            value={bulkText}
            onChange={(e) => setBulkText(e.target.value)}
          />
          <button type="submit">Import</button>
          {bulkResult && (
            <div className="bulk-import-result">
              <p>
                {bulkResult.created} created, {bulkResult.updated} updated, {bulkResult.errors} errors
              </p>
              {bulkResult.errors > 0 && (
                <ul>
                  {bulkResult.results
                    .filter((r) => r.action === "error")
                    .map((r, i) => (
                      <li key={i}>
                        {r.drop_number}: {r.detail}
                      </li>
                    ))}
                </ul>
              )}
            </div>
          )}
        </form>
      )}
    </div>
  );
}
