import { WorkflowBadge } from "./WorkflowBadge";

export function SiteList({ sites, onSelect, selectedId }) {
  if (sites.length === 0) {
    return <p className="empty-state">No sites yet. Add one to get started.</p>;
  }

  return (
    <table className="site-table">
      <thead>
        <tr>
          <th>Building Code</th>
          <th>Name</th>
          <th>Rack ID</th>
          <th>District</th>
          <th>Stage</th>
        </tr>
      </thead>
      <tbody>
        {sites.map((site) => (
          <tr
            key={site.id}
            className={site.id === selectedId ? "site-row site-row--selected" : "site-row"}
            onClick={() => onSelect(site)}
          >
            <td>{site.building_code}</td>
            <td>{site.name}</td>
            <td>{site.rack_id || "—"}</td>
            <td>{site.district || "—"}</td>
            <td>
              <WorkflowBadge stage={site.workflow_stage} />
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
