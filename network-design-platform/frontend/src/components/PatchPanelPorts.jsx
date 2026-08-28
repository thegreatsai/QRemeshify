import { useEffect, useState } from "react";
import { api } from "../api/client";

/**
 * Port grid for a patch panel. A port's occupant is read straight from
 * CableDrop.port_id -- the exact field the Drop List reads too -- so
 * assigning, moving, or unassigning a drop here shows up there instantly,
 * with no separate sync step (the old workbook's 'TransposeValuesOnly'
 * macro was a manual stand-in for this).
 */
export function PatchPanelPorts({ siteId, panelId, panelName, refreshSignal, onChange }) {
  const [panel, setPanel] = useState(null);
  const [unassignedDrops, setUnassignedDrops] = useState([]);
  const [freePorts, setFreePorts] = useState([]);
  const [activePortId, setActivePortId] = useState(null);
  const [pickDropId, setPickDropId] = useState("");
  const [newDropNumber, setNewDropNumber] = useState("");
  const [movePortId, setMovePortId] = useState("");
  const [error, setError] = useState(null);

  const refresh = () => {
    api.getPatchPanel(panelId).then(setPanel);
    api.listCableDrops(siteId).then((drops) => setUnassignedDrops(drops.filter((d) => !d.port_location)));
    api.listSitePorts(siteId, true).then(setFreePorts);
  };

  useEffect(() => {
    refresh();
    setActivePortId(null);
  }, [panelId]);

  // A shared-refresh tick from elsewhere (e.g. the Drop List) should just
  // re-fetch this panel's ports, not close whichever port the user has open.
  useEffect(() => {
    if (refreshSignal !== undefined) refresh();
  }, [refreshSignal]);

  if (!panel) return null;

  const notify = () => {
    refresh();
    onChange();
  };

  const openPort = (port) => {
    setActivePortId(activePortId === port.id ? null : port.id);
    setError(null);
    setPickDropId("");
    setNewDropNumber("");
    setMovePortId("");
  };

  const assignExisting = async (e) => {
    e.preventDefault();
    if (!pickDropId) return;
    setError(null);
    try {
      await api.assignCableDrop(Number(pickDropId), activePortId);
      notify();
      setActivePortId(null);
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
      await api.assignCableDrop(drop.id, activePortId);
      notify();
      setActivePortId(null);
    } catch (err) {
      setError(err.message);
    }
  };

  const unassign = async (dropId) => {
    setError(null);
    try {
      await api.unassignCableDrop(dropId);
      notify();
      setActivePortId(null);
    } catch (err) {
      setError(err.message);
    }
  };

  const moveTo = async (e) => {
    e.preventDefault();
    if (!movePortId) return;
    const port = panel.ports.find((p) => p.id === activePortId);
    if (!port?.cable_drop) return;
    setError(null);
    try {
      await api.assignCableDrop(port.cable_drop.id, Number(movePortId));
      notify();
      setActivePortId(null);
    } catch (err) {
      setError(err.message);
    }
  };

  const activePort = panel.ports.find((p) => p.id === activePortId);

  return (
    <div className="patch-panel-ports">
      <h5>
        {panelName} — {panel.port_count} ports
      </h5>
      {error && <p className="form-error">{error}</p>}
      <div className="port-grid">
        {panel.ports.map((port) => (
          <button
            key={port.id}
            type="button"
            className={`port port--${port.status}${activePortId === port.id ? " port--editing" : ""}`}
            title={port.cable_drop ? `Drop ${port.cable_drop.drop_number}` : `Port ${port.port_number}`}
            onClick={() => openPort(port)}
          >
            {port.cable_drop ? port.cable_drop.drop_number : port.port_number}
          </button>
        ))}
      </div>

      {activePort && (
        <div className="port-editor">
          <strong>Port {activePort.port_number}</strong>

          {activePort.cable_drop ? (
            <>
              <p>
                Patched to drop <strong>{activePort.cable_drop.drop_number}</strong>
              </p>
              <div className="inline-form">
                <button type="button" onClick={() => unassign(activePort.cable_drop.id)}>
                  Unassign
                </button>
                <form className="inline-form" onSubmit={moveTo}>
                  <select value={movePortId} onChange={(e) => setMovePortId(e.target.value)}>
                    <option value="">Move to port...</option>
                    {freePorts.map((p) => (
                      <option key={p.port_id} value={p.port_id}>
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
                  <option value="">Assign existing drop...</option>
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
