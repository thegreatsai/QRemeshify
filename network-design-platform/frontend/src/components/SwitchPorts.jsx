import { useEffect, useState } from "react";
import { api } from "../api/client";

/**
 * Port grid for a switch: VLAN/mode/description config per port, plus the
 * same drop cross-connect pattern PatchPanelPorts uses (assign/move/
 * unassign a CableDrop, reading/writing CableDrop.switch_port_id -- the
 * single source of truth also read by the Drop List's "Switch Port"
 * column). Replaces the hand-typed rows in 'VLAN Config (9300)' /
 * 'VLAN Config (2960)'.
 */
export function SwitchPorts({ siteId, switchId, switchName, refreshSignal, onChange }) {
  const [switchData, setSwitchData] = useState(null);
  const [vlans, setVlans] = useState([]);
  const [unassignedDrops, setUnassignedDrops] = useState([]);
  const [freeSwitchPorts, setFreeSwitchPorts] = useState([]);
  const [activePortId, setActivePortId] = useState(null);
  const [configDraft, setConfigDraft] = useState({ vlan_id: "", mode: "access", description: "" });
  const [pickDropId, setPickDropId] = useState("");
  const [newDropNumber, setNewDropNumber] = useState("");
  const [movePortId, setMovePortId] = useState("");
  const [error, setError] = useState(null);

  const refresh = () => {
    api.getSwitch(switchId).then(setSwitchData);
    api.listVlans(siteId).then(setVlans);
    api.listCableDrops(siteId).then((drops) => setUnassignedDrops(drops.filter((d) => !d.switch_port_location)));
    api.listSiteSwitchPorts(siteId, true).then(setFreeSwitchPorts);
  };

  useEffect(() => {
    refresh();
    setActivePortId(null);
  }, [switchId]);

  useEffect(() => {
    if (refreshSignal !== undefined) refresh();
  }, [refreshSignal]);

  if (!switchData) return null;

  const notify = () => {
    refresh();
    onChange();
  };

  const openPort = (port) => {
    setActivePortId(activePortId === port.id ? null : port.id);
    setError(null);
    setConfigDraft({
      vlan_id: port.vlan?.id ?? "",
      mode: port.mode,
      description: port.description ?? "",
    });
    setPickDropId("");
    setNewDropNumber("");
    setMovePortId("");
  };

  const saveConfig = async (e) => {
    e.preventDefault();
    setError(null);
    try {
      await api.updateSwitchPort(switchId, activePortId, {
        vlan_id: configDraft.vlan_id ? Number(configDraft.vlan_id) : null,
        mode: configDraft.mode,
        description: configDraft.description || null,
      });
      notify();
    } catch (err) {
      setError(err.message);
    }
  };

  const assignExisting = async (e) => {
    e.preventDefault();
    if (!pickDropId) return;
    setError(null);
    try {
      await api.assignCableDropSwitchPort(Number(pickDropId), activePortId);
      notify();
    } catch (err) {
      setError(err.message);
    }
  };

  const createAndAssign = async (e) => {
    e.preventDefault();
    if (!newDropNumber) return;
    setError(null);
    try {
      const drop = await api.createCableDrop(siteId, { drop_number: newDropNumber });
      await api.assignCableDropSwitchPort(drop.id, activePortId);
      setNewDropNumber("");
      notify();
    } catch (err) {
      setError(err.message);
    }
  };

  const unassignDrop = async (dropId) => {
    setError(null);
    try {
      await api.unassignCableDropSwitchPort(dropId);
      notify();
    } catch (err) {
      setError(err.message);
    }
  };

  const moveTo = async (e) => {
    e.preventDefault();
    if (!movePortId) return;
    const port = switchData.ports.find((p) => p.id === activePortId);
    if (!port?.cable_drop) return;
    setError(null);
    try {
      await api.assignCableDropSwitchPort(port.cable_drop.id, Number(movePortId));
      notify();
    } catch (err) {
      setError(err.message);
    }
  };

  const downloadConfig = async () => {
    setError(null);
    try {
      const res = await fetch(api.switchExportUrl(switchId));
      if (!res.ok) throw new Error(`Export failed with ${res.status}`);
      const contentType = res.headers.get("content-type") || "";
      const ext = contentType.includes("json") ? "json" : "txt";
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${switchName.replace(/\s+/g, "_")}-config.${ext}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err.message);
    }
  };

  const activePort = switchData.ports.find((p) => p.id === activePortId);

  return (
    <div className="patch-panel-ports">
      <h5>
        {switchName} — {switchData.model} — {switchData.port_count} ports
        <button type="button" className="download-config-btn" onClick={downloadConfig}>
          Download Config
        </button>
      </h5>
      {error && <p className="form-error">{error}</p>}
      <div className="port-grid">
        {switchData.ports.map((port) => (
          <button
            key={port.id}
            type="button"
            className={`port port--switch port--mode-${port.mode}${port.cable_drop ? " port--patched" : ""}${
              activePortId === port.id ? " port--editing" : ""
            }`}
            title={
              (port.cable_drop ? `Drop ${port.cable_drop.drop_number}` : `Port ${port.port_number}`) +
              (port.vlan ? ` (VLAN ${port.vlan.vlan_number})` : "")
            }
            onClick={() => openPort(port)}
          >
            {port.cable_drop ? port.cable_drop.drop_number : port.port_number}
          </button>
        ))}
      </div>

      {activePort && (
        <div className="port-editor">
          <strong>Port {activePort.port_number}</strong>

          <form className="inline-form" onSubmit={saveConfig}>
            <select
              value={configDraft.mode}
              onChange={(e) => setConfigDraft((d) => ({ ...d, mode: e.target.value }))}
            >
              <option value="access">Access</option>
              <option value="trunk">Trunk</option>
            </select>
            <select
              value={configDraft.vlan_id}
              onChange={(e) => setConfigDraft((d) => ({ ...d, vlan_id: e.target.value }))}
              disabled={configDraft.mode === "trunk"}
            >
              <option value="">No VLAN</option>
              {vlans.map((v) => (
                <option key={v.id} value={v.id}>
                  VLAN {v.vlan_number} — {v.name}
                </option>
              ))}
            </select>
            <input
              placeholder="Description"
              value={configDraft.description}
              onChange={(e) => setConfigDraft((d) => ({ ...d, description: e.target.value }))}
            />
            <button type="submit">Save Config</button>
          </form>

          {activePort.cable_drop ? (
            <>
              <p>
                Cross-connected to drop <strong>{activePort.cable_drop.drop_number}</strong>
              </p>
              <div className="inline-form">
                <button type="button" onClick={() => unassignDrop(activePort.cable_drop.id)}>
                  Unassign
                </button>
                <form className="inline-form" onSubmit={moveTo}>
                  <select value={movePortId} onChange={(e) => setMovePortId(e.target.value)}>
                    <option value="">Move to port...</option>
                    {freeSwitchPorts.map((p) => (
                      <option key={p.switch_port_id} value={p.switch_port_id}>
                        {p.rack_number} / {p.rack_item_name} / Port {p.port_number}
                      </option>
                    ))}
                  </select>
                  <button type="submit" disabled={!movePortId}>
                    Move
                  </button>
                </form>
              </div>
            </>
          ) : (
            <div className="inline-form">
              <form className="inline-form" onSubmit={assignExisting}>
                <select value={pickDropId} onChange={(e) => setPickDropId(e.target.value)}>
                  <option value="">Cross-connect existing drop...</option>
                  {unassignedDrops.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.drop_number}
                    </option>
                  ))}
                </select>
                <button type="submit" disabled={!pickDropId}>
                  Assign
                </button>
              </form>
              <form className="inline-form" onSubmit={createAndAssign}>
                <input
                  placeholder="New drop number"
                  value={newDropNumber}
                  onChange={(e) => setNewDropNumber(e.target.value)}
                />
                <button type="submit" disabled={!newDropNumber}>
                  Create &amp; Assign
                </button>
              </form>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
