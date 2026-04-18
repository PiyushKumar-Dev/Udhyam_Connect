import { Fragment } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import { useState } from "react";

import type { SourceRecord } from "../types";
import { ConfidenceBadge } from "./ConfidenceBadge";
import { JsonTree } from "./JsonTree";

interface LinkedRecordsProps {
  records: SourceRecord[];
  canonicalName: string;
}

export function LinkedRecords({ records, canonicalName }: LinkedRecordsProps) {
  const [openRows, setOpenRows] = useState<Record<string, boolean>>({});

  return (
    <div className="overflow-hidden rounded-2xl border border-border bg-white">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-border">
          <thead className="bg-slate-50">
            <tr className="text-left text-xs uppercase tracking-wide text-muted">
              <th className="px-4 py-3" />
              <th className="px-4 py-3">Source System</th>
              <th className="px-4 py-3">Original Name</th>
              <th className="px-4 py-3">Address</th>
              <th className="px-4 py-3">PAN</th>
              <th className="px-4 py-3">GSTIN</th>
              <th className="px-4 py-3">Match Confidence</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border text-sm text-slate-700">
            {records.map((record) => {
              const isOpen = openRows[record.id] ?? false;
              const differentFromCanonical =
                record.norm_name.split(" ").join("") !== canonicalName.split(" ").join("");

              return (
                <Fragment key={record.id}>
                  <tr className="hover:bg-slate-50">
                    <td className="px-4 py-3">
                      <button
                        className="rounded-full border border-border p-1"
                        onClick={() =>
                          setOpenRows((current) => ({
                            ...current,
                            [record.id]: !current[record.id]
                          }))
                        }
                        type="button"
                      >
                        {isOpen ? (
                          <ChevronDown className="h-4 w-4" />
                        ) : (
                          <ChevronRight className="h-4 w-4" />
                        )}
                      </button>
                    </td>
                    <td className="px-4 py-3 font-semibold">{record.source_system}</td>
                    <td className={`px-4 py-3 ${differentFromCanonical ? "text-warning" : ""}`}>
                      {record.raw_name}
                    </td>
                    <td className="px-4 py-3">{record.raw_address}</td>
                    <td className="px-4 py-3 font-mono text-xs">{record.pan ?? "N/A"}</td>
                    <td className="px-4 py-3 font-mono text-xs">{record.gstin ?? "N/A"}</td>
                    <td className="px-4 py-3">
                      {record.match_confidence !== null && record.match_confidence !== undefined ? (
                        <ConfidenceBadge value={record.match_confidence} />
                      ) : (
                        "N/A"
                      )}
                    </td>
                  </tr>
                  {isOpen && (
                    <tr className="bg-slate-50">
                      <td className="px-4 py-4" colSpan={7}>
                        <JsonTree data={record.raw_payload} label="raw_payload" />
                      </td>
                    </tr>
                  )}
                </Fragment>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
