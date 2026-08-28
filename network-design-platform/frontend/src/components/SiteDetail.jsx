import { useEffect, useState } from "react";
import { api } from "../api/client";
import { ReferenceSelect } from "./ReferenceSelect";
import { WorkflowBadge } from "./WorkflowBadge";

export function SiteDetail({ site }) {
  const [rooms, setRooms] = useState([]);
  const [racks, setRacks] = useState([]);
  const [newRoomName, setNewRoomName] = useState("");
  const [newRoomType, setNewRoomType] = useState("");
  const [newRackNumber, setNewRackNumber] = useState("");

  const refresh = () => {
    api.listRooms(site.id).then(setRooms);
    api.listRacks(site.id).then(setRacks);
  };

  useEffect(refresh, [site.id]);

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
    await api.createRack(site.id, { rack_number: newRackNumber });
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
            <li key={rack.id}>{rack.rack_number}</li>
          ))}
        </ul>
        <form className="inline-form" onSubmit={addRack}>
          <input
            placeholder="Rack number"
            value={newRackNumber}
            onChange={(e) => setNewRackNumber(e.target.value)}
          />
          <button type="submit">Add Rack</button>
        </form>
      </section>
    </div>
  );
}
