import { useState } from "react";
import { api } from "../api/client";

/**
 * Stateless "how many switches do I need" calculator -- replaces the old
 * 'Switch & Port Allocation' sheet's formula wall. Doesn't read a site's
 * actual drop counts (nothing in the data model tags a drop as an
 * "AP drop" yet), so it's a what-if tool during design rather than a
 * live report.
 */
export function PortAllocationCalculator() {
  const [form, setForm] = useState({
    data_drops: "",
    ap_drops: "",
    ports_per_switch: "48",
    ap_reserved_ports_per_switch: "0",
    uplink_ports_per_switch: "2",
  });
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const calculate = async (e) => {
    e.preventDefault();
    setError(null);
    try {
      const body = await api.calculatePortAllocation({
        data_drops: Number(form.data_drops) || 0,
        ap_drops: Number(form.ap_drops) || 0,
        ports_per_switch: Number(form.ports_per_switch) || 48,
        ap_reserved_ports_per_switch: Number(form.ap_reserved_ports_per_switch) || 0,
        uplink_ports_per_switch: Number(form.uplink_ports_per_switch) || 0,
      });
      setResult(body);
    } catch (err) {
      setError(err.message);
      setResult(null);
    }
  };

  return (
    <div className="port-allocation-calculator">
      <form className="inline-form calculator-form" onSubmit={calculate}>
        <label>
          Data drops
          <input
            type="number"
            min="0"
            value={form.data_drops}
            onChange={(e) => setForm((f) => ({ ...f, data_drops: e.target.value }))}
          />
        </label>
        <label>
          AP drops
          <input
            type="number"
            min="0"
            value={form.ap_drops}
            onChange={(e) => setForm((f) => ({ ...f, ap_drops: e.target.value }))}
          />
        </label>
        <label>
          Ports/switch
          <input
            type="number"
            min="1"
            value={form.ports_per_switch}
            onChange={(e) => setForm((f) => ({ ...f, ports_per_switch: e.target.value }))}
          />
        </label>
        <label>
          AP-reserved/switch
          <input
            type="number"
            min="0"
            value={form.ap_reserved_ports_per_switch}
            onChange={(e) => setForm((f) => ({ ...f, ap_reserved_ports_per_switch: e.target.value }))}
          />
        </label>
        <label>
          Uplink ports/switch
          <input
            type="number"
            min="0"
            value={form.uplink_ports_per_switch}
            onChange={(e) => setForm((f) => ({ ...f, uplink_ports_per_switch: e.target.value }))}
          />
        </label>
        <button type="submit">Calculate</button>
      </form>

      {error && <p className="form-error">{error}</p>}

      {result && (
        <div className="calculator-result">
          <p>
            <strong>{result.switches_needed}</strong> switch(es) needed —{" "}
            {result.usable_data_ports_per_switch} usable data ports/switch
          </p>
          <table className="drop-table">
            <thead>
              <tr>
                <th>Switch</th>
                <th>Data Ports</th>
                <th>AP Ports</th>
                <th>Total</th>
              </tr>
            </thead>
            <tbody>
              {result.per_switch.map((p) => (
                <tr key={p.switch_index}>
                  <td>#{p.switch_index}</td>
                  <td>{p.data_ports}</td>
                  <td>{p.ap_ports}</td>
                  <td>{p.total_ports}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
