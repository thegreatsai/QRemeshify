import { useEffect, useState } from "react";
import { api } from "../api/client";
import { DropList } from "./DropList";
import { RackElevation } from "./RackElevation";
import { ReferenceSelect } from "./ReferenceSelect";
import { WorkflowBadge } from "./WorkflowBadge";

export function SiteDetail({ site }) {
  const [rooms, setRooms] = useState([]);
  const [racks, setRacks] = useState([]);
  const [newRoomName, setNewRoomName] = useState("");
  const [newRoomType, setNewRoomType] = useState("");
  const [newRackNumber, setNewRackNumber] = useState("");
  const [newRackTotalU, setNewRackTotalU] = useState("42");
  const [selectedRack, setSelectedRack] = useState(null);

  // Bumped by RackElevation/PatchPanelPorts and DropList whenever either
  // mutates a cable-drop or port assignment. Both read it as an effect
  // dependency to refetch -- so a move made in one view shows up in the
  // other immediately, with no separate sync step.
  const [dataVersion, setDataVersion] = useState(0);
  const bump = () => setDataVersion((v) => v + 1);

  const refresh = () => {
    api.listRooms(site.id).then(setRooms);
    api.listRacks(site.id).then(setRacks);
  };

  useEffect(() => {
    refresh();
    setSelectedRack(null);
  }, [site.id]);

  const addRoom = async (e) => {
    e.preventDefault();
    if (!newRoomName) return;
    await api.createRoom(site.id, { name: newRoomName, room_type_value: newRoomType || null });
    setNewRoomName("");
    setNewRoomType("");
    refresh();
  };

  const addRack = async (e) => {
    e.preventDefault();
    if (!newRackNumber) return;
    await api.createRack(site.id, { rack_number: newRackNumber, total_u: Number(newRackTotalU) || 42 });
    setNewRackNumber("");
    refresh();
  };

  return (
    <div className="site-detail">
      <header>
        <h2>
          {site.name} <WorkflowBadge stage={site.workflow_stage} />
        </h2>
        <p className="site-meta">
          {site.building_code} · Rack {site.rack_id || "—"} · District {site.district || "—"}
        </p>
      </header>

      <section>
        <h3>Rooms</h3>
        <ul className="entity-list">
          {rooms.map((room) => (
            <li key={room.id}>
              {room.name} {room.room_type_value && <span className="tag">{room.room_type_value}</span>}
            </li>
          ))}
        </ul>
        <form className="inline-form" onSubmit={addRoom}>
          <input
            placeholder="Room name"
            value={newRoomName}
            onChange={(e) => setNewRoomName(e.target.value)}
          />
          <ReferenceSelect listKey="room_type" value={newRoomType} onChange={setNewRoomType} />
          <button type="submit">Add Room</button>
        </form>
      </section>

      <section>
        <h3>Racks</h3>
        <ul className="entity-list">
          {racks.map((rack) => (
            <li
              key={rack.id}
              className={rack.id === selectedRack?.id ? "entity-list-item--selected" : ""}
              onClick={() => setSelectedRack(rack)}
            >
              {rack.rack_number} <span className="tag">{rack.total_u}U</span>
            </li>
          ))}
        </ul>
        <form className="inline-form" onSubmit={addRack}>
          <input
            placeholder="Rack number"
            value={newRackNumber}
            onChange={(e) => setNewRackNumber(e.target.value)}
          />
          <input
            type="number"
            min="1"
            title="Total U"
            value={newRackTotalU}
            onChange={(e) => setNewRackTotalU(e.target.value)}
          />
          <button type="submit">Add Rack</button>
        </form>

        {selectedRack && (
          <RackElevation rack={selectedRack} refreshSignal={dataVersion} onChange={bump} />
        )}
      </section>

      <section>
        <h3>Drop List</h3>
        <DropList site={site} rooms={rooms} refreshSignal={dataVersion} onChange={bump} />
      </section>
    </div>
  );
}
