import { AlertTriangle, BadgeCheck, Bolt, FileWarning, Shield } from "lucide-react";

import type { ActivityTimelineEvent } from "../types";

function iconForEvent(eventType: string) {
  if (eventType === "RENEWAL") {
    return <BadgeCheck className="h-4 w-4" />;
  }
  if (eventType === "INSPECTION") {
    return <Shield className="h-4 w-4" />;
  }
  if (eventType === "ELECTRICITY") {
    return <Bolt className="h-4 w-4" />;
  }
  if (eventType === "CANCELLED" || eventType === "SURRENDERED") {
    return <FileWarning className="h-4 w-4" />;
  }
  return <AlertTriangle className="h-4 w-4" />;
}

function colorForEvent(eventType: string) {
  if (eventType === "RENEWAL" || eventType === "ELECTRICITY") {
    return "border-green-200 bg-green-50 text-success";
  }
  if (eventType === "INSPECTION") {
    return "border-amber-200 bg-amber-50 text-warning";
  }
  return "border-red-200 bg-red-50 text-danger";
}

export function EvidenceTimeline({ events }: { events: ActivityTimelineEvent[] }) {
  return (
    <div className="space-y-4">
      {events.map((event) => (
        <div className="flex gap-4" key={event.id}>
          <div className="flex flex-col items-center">
            <div className={`rounded-full border p-2 ${colorForEvent(event.event_type)}`}>
              {iconForEvent(event.event_type)}
            </div>
            <div className="mt-2 h-full w-px bg-border" />
          </div>
          <div className="pb-6">
            <p className="text-sm font-semibold text-slate-900">
              {new Date(event.event_date).toLocaleDateString()} | {event.event_type}
            </p>
            <p className="text-xs uppercase tracking-wide text-muted">{event.source}</p>
            <p className="mt-2 text-sm text-slate-700">{event.summary}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
