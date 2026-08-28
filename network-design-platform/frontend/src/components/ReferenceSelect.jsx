import { useEffect, useState } from "react";
import { api } from "../api/client";

/**
 * Dropdown backed by a reference_list/reference_item pair -- the live
 * replacement for a single column of the old workbook's "Data Lists" sheet.
 * New options are added with a database row, not distributed as a sheet
 * edit to every site file.
 */
export function ReferenceSelect({ listKey, value, onChange, placeholder = "Select..." }) {
  const [items, setItems] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    api
      .getReferenceList(listKey)
      .then((list) => {
        if (!cancelled) setItems(list.items);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message);
      });
    return () => {
      cancelled = true;
    };
  }, [listKey]);

  if (error) {
    return <span className="reference-select-error">Couldn't load "{listKey}" options</span>;
  }

  return (
    <select
      className="reference-select"
      value={value ?? ""}
      onChange={(e) => onChange(e.target.value)}
    >
      <option value="" disabled>
        {placeholder}
      </option>
      {items.map((item) => (
        <option key={item.id} value={item.value}>
          {item.label}
        </option>
      ))}
    </select>
  );
}
