import { useEffect, useState } from "react";
import { api } from "./api/client";
import { SiteDetail } from "./components/SiteDetail";
import { SiteForm } from "./components/SiteForm";
import { SiteList } from "./components/SiteList";

export default function App() {
  const [sites, setSites] = useState([]);
  const [selected, setSelected] = useState(null);
  const [loadError, setLoadError] = useState(null);

  const refresh = () => {
    api
      .listSites()
      .then((data) => {
        setSites(data);
        setLoadError(null);
      })
      .catch((err) => setLoadError(err.message));
  };

  useEffect(refresh, []);

  return (
    <div className="app">
      <header className="app-header">
        <h1>Network Design Platform</h1>
        <p className="subtitle">Multi-site network design &amp; as-built documentation</p>
      </header>

      {loadError && <p className="form-error">Couldn't reach the API: {loadError}</p>}

      <div className="app-layout">
        <div className="app-main">
          <SiteList sites={sites} onSelect={setSelected} selectedId={selected?.id} />
          {selected && <SiteDetail site={selected} />}
        </div>
        <aside className="app-sidebar">
          <SiteForm
            onCreated={(site) => {
              refresh();
              setSelected(site);
            }}
          />
        </aside>
      </div>
    </div>
  );
}
