import { Search } from "lucide-react";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { useSearch } from "../api/hooks";
import { EntityCard } from "./EntityCard";

export function SearchBar() {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const [focused, setFocused] = useState(false);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setDebouncedQuery(query.trim());
    }, 300);
    return () => window.clearTimeout(timer);
  }, [query]);

  const searchResults = useSearch(debouncedQuery);

  return (
    <div className="relative">
      <div className="flex items-center gap-3 rounded-2xl border border-border bg-white px-4 py-3 shadow-panel">
        <Search className="h-5 w-5 text-primary" />
        <input
          className="w-full border-none bg-transparent text-sm outline-none placeholder:text-muted"
          onBlur={() => window.setTimeout(() => setFocused(false), 150)}
          onChange={(event) => setQuery(event.target.value)}
          onFocus={() => setFocused(true)}
          placeholder="Search by name, GSTIN, PAN, or UBID..."
          value={query}
        />
      </div>

      {focused && debouncedQuery.length > 1 && (
        <div className="absolute z-20 mt-3 w-full space-y-2 rounded-2xl border border-border bg-white p-3 shadow-panel">
          {searchResults.data?.length ? (
            searchResults.data.map((entity) => (
              <EntityCard
                entity={entity}
                key={entity.ubid}
                onSelect={(ubid) => {
                  navigate(`/entity/${ubid}`);
                  setFocused(false);
                  setQuery("");
                  setDebouncedQuery("");
                }}
              />
            ))
          ) : (
            <p className="px-2 py-3 text-sm text-muted">No matching businesses found.</p>
          )}
        </div>
      )}
    </div>
  );
}
