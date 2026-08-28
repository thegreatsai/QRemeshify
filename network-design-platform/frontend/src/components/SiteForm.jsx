import { useState } from "react";
import { api } from "../api/client";

export function SiteForm({ onCreated }) {
  const [form, setForm] = useState({ building_code: "", rack_id: "", name: "", district: "" });
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const set = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));

  const submit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const site = await api.createSite(form);
      setForm({ building_code: "", rack_id: "", name: "", district: "" });
      onCreated(site);
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form className="site-form" onSubmit={submit}>
      <h2>New Site</h2>
      <label>
        Building Code
        <input value={form.building_code} onChange={set("building_code")} required />
      </label>
      <label>
        Rack ID
        <input value={form.rack_id} onChange={set("rack_id")} />
      </label>
      <label>
        Name
        <input value={form.name} onChange={set("name")} required />
      </label>
      <label>
        District
        <input value={form.district} onChange={set("district")} />
      </label>
      {error && <p className="form-error">{error}</p>}
      <button type="submit" disabled={submitting}>
        {submitting ? "Creating..." : "Create Site"}
      </button>
    </form>
  );
}
