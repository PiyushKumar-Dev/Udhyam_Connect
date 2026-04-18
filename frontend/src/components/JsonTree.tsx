import { ChevronDown, ChevronRight } from "lucide-react";
import { useState } from "react";

function isObject(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

export function JsonTree({ data, label = "root" }: { data: unknown; label?: string }) {
  const [open, setOpen] = useState(label === "root");

  if (Array.isArray(data)) {
    return (
      <div className="pl-4">
        <button
          className="flex items-center gap-2 text-sm font-semibold text-slate-800"
          onClick={() => setOpen((value) => !value)}
          type="button"
        >
          {open ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
          {label} [{data.length}]
        </button>
        {open && (
          <div className="mt-2 space-y-2 border-l border-border pl-4">
            {data.map((item, index) => (
              <JsonTree data={item} key={`${label}-${index}`} label={`${index}`} />
            ))}
          </div>
        )}
      </div>
    );
  }

  if (isObject(data)) {
    return (
      <div className="pl-4">
        <button
          className="flex items-center gap-2 text-sm font-semibold text-slate-800"
          onClick={() => setOpen((value) => !value)}
          type="button"
        >
          {open ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
          {label}
        </button>
        {open && (
          <div className="mt-2 space-y-2 border-l border-border pl-4">
            {Object.entries(data).map(([key, value]) => (
              <JsonTree data={value} key={key} label={key} />
            ))}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="pl-4 text-sm text-slate-700">
      <span className="font-semibold text-slate-900">{label}:</span> {String(data)}
    </div>
  );
}
