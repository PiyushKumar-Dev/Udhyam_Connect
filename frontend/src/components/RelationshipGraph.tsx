import { useCallback, useEffect, useRef, useState } from "react";
import type { GraphEdge, GraphNode } from "../types";

interface RelationshipGraphProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

const nodeColors: Record<GraphNode["node_type"], string> = {
  business: "#1d4ed8",
  record: "#0f766e",
  activity: "#d97706",
  review: "#dc2626"
};

const edgeColors: Record<string, string> = {
  contains_record: "#0d9488",
  activity_signal: "#d97706",
  review_task: "#dc2626",
  match_pair: "#7c3aed"
};

interface SimNode {
  id: string;
  x: number;
  y: number;
  vx: number;
  vy: number;
  node: GraphNode;
  radius: number;
}

function buildSimulation(
  nodes: GraphNode[],
  edges: GraphEdge[],
  width: number,
  height: number
): SimNode[] {
  const cx = width / 2;
  const cy = height / 2;

  // Place focus node at center, others spread in a circle with jitter
  const simNodes: SimNode[] = nodes.map((node, i) => {
    const isFocus = node.emphasis === "focus";
    const r = node.node_type === "business" ? 30 : node.node_type === "review" ? 18 : 22;
    if (isFocus) {
      return { id: node.id, x: cx, y: cy, vx: 0, vy: 0, node, radius: r };
    }
    const angle = (Math.PI * 2 * i) / Math.max(nodes.length - 1, 1) + (Math.random() - 0.5) * 0.3;
    const dist = 120 + Math.random() * 100;
    return {
      id: node.id,
      x: cx + Math.cos(angle) * dist,
      y: cy + Math.sin(angle) * dist,
      vx: 0,
      vy: 0,
      node,
      radius: r,
    };
  });

  const nodeMap = new Map(simNodes.map((n) => [n.id, n]));

  // Simple force-directed: iterate 120 times
  const iterations = 120;
  const repulsion = 5000;
  const attraction = 0.015;
  const idealEdgeLen = 120;
  const damping = 0.85;

  for (let iter = 0; iter < iterations; iter++) {
    // Repulsion between all pairs
    for (let i = 0; i < simNodes.length; i++) {
      for (let j = i + 1; j < simNodes.length; j++) {
        const a = simNodes[i];
        const b = simNodes[j];
        const dx = b.x - a.x;
        const dy = b.y - a.y;
        const dist = Math.max(Math.sqrt(dx * dx + dy * dy), 1);
        const force = repulsion / (dist * dist);
        const fx = (dx / dist) * force;
        const fy = (dy / dist) * force;
        a.vx -= fx;
        a.vy -= fy;
        b.vx += fx;
        b.vy += fy;
      }
    }

    // Attraction along edges
    for (const edge of edges) {
      const a = nodeMap.get(edge.source);
      const b = nodeMap.get(edge.target);
      if (!a || !b) continue;
      const dx = b.x - a.x;
      const dy = b.y - a.y;
      const dist = Math.max(Math.sqrt(dx * dx + dy * dy), 1);
      const force = (dist - idealEdgeLen) * attraction;
      const fx = (dx / dist) * force;
      const fy = (dy / dist) * force;
      a.vx += fx;
      a.vy += fy;
      b.vx -= fx;
      b.vy -= fy;
    }

    // Center gravity
    for (const n of simNodes) {
      n.vx += (cx - n.x) * 0.002;
      n.vy += (cy - n.y) * 0.002;
    }

    // Apply velocity, pin focus
    for (const n of simNodes) {
      if (n.node.emphasis === "focus") {
        n.x = cx;
        n.y = cy;
        n.vx = 0;
        n.vy = 0;
        continue;
      }
      n.vx *= damping;
      n.vy *= damping;
      n.x += n.vx;
      n.y += n.vy;
      // Keep in bounds
      n.x = Math.max(n.radius + 40, Math.min(width - n.radius - 40, n.x));
      n.y = Math.max(n.radius + 40, Math.min(height - n.radius - 40, n.y));
    }
  }
  return simNodes;
}

function curvedPath(x1: number, y1: number, x2: number, y2: number): string {
  const mx = (x1 + x2) / 2;
  const my = (y1 + y2) / 2;
  const dx = x2 - x1;
  const dy = y2 - y1;
  const dist = Math.sqrt(dx * dx + dy * dy);
  const offset = Math.min(dist * 0.15, 30);
  const cx = mx - (dy / dist) * offset;
  const cy = my + (dx / dist) * offset;
  return `M ${x1} ${y1} Q ${cx} ${cy} ${x2} ${y2}`;
}

export function RelationshipGraph({ nodes, edges }: RelationshipGraphProps) {
  const width = 860;
  const height = 580;
  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null);
  const [zoom, setZoom] = useState(1);
  const [tooltip, setTooltip] = useState<{ x: number; y: number; node: GraphNode } | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const simNodes = useCallback(() => buildSimulation(nodes, edges, width, height), [nodes, edges])();
  const posMap = new Map(simNodes.map((sn) => [sn.id, sn]));

  const connectedIds = new Set<string>();
  if (hoveredNodeId) {
    connectedIds.add(hoveredNodeId);
    for (const e of edges) {
      if (e.source === hoveredNodeId) connectedIds.add(e.target);
      if (e.target === hoveredNodeId) connectedIds.add(e.source);
    }
  }

  const handleNodeHover = (sn: SimNode | null, event?: React.MouseEvent) => {
    if (sn && event && containerRef.current) {
      const rect = containerRef.current.getBoundingClientRect();
      setTooltip({
        x: event.clientX - rect.left,
        y: event.clientY - rect.top - 12,
        node: sn.node,
      });
      setHoveredNodeId(sn.id);
    } else {
      setTooltip(null);
      setHoveredNodeId(null);
    }
  };

  return (
    <div ref={containerRef} className="relative overflow-hidden rounded-[28px] border border-border bg-[linear-gradient(180deg,#f8fbff_0%,#eef5ff_52%,#fdfefe_100%)] p-2">
      {/* Zoom controls */}
      <div className="absolute right-4 top-4 z-10 flex flex-col gap-1">
        <button
          className="flex h-8 w-8 items-center justify-center rounded-xl border border-border bg-white text-sm font-bold text-slate-700 shadow-sm hover:bg-slate-50"
          onClick={() => setZoom((z) => Math.min(z + 0.15, 2))}
          type="button"
        >
          +
        </button>
        <button
          className="flex h-8 w-8 items-center justify-center rounded-xl border border-border bg-white text-sm font-bold text-slate-700 shadow-sm hover:bg-slate-50"
          onClick={() => setZoom((z) => Math.max(z - 0.15, 0.5))}
          type="button"
        >
          −
        </button>
        <button
          className="flex h-8 w-8 items-center justify-center rounded-xl border border-border bg-white text-[10px] font-bold text-slate-500 shadow-sm hover:bg-slate-50"
          onClick={() => setZoom(1)}
          type="button"
        >
          1:1
        </button>
      </div>

      {/* Tooltip */}
      {tooltip && (
        <div
          className="pointer-events-none absolute z-20 rounded-2xl border border-border bg-white px-4 py-3 shadow-lg"
          style={{ left: tooltip.x + 16, top: tooltip.y - 40 }}
        >
          <p className="text-sm font-semibold text-slate-900">{tooltip.node.label}</p>
          {tooltip.node.subtitle && (
            <p className="mt-0.5 text-xs text-muted">{tooltip.node.subtitle}</p>
          )}
          <span
            className="mt-1 inline-block rounded-full px-2 py-0.5 text-[10px] font-semibold text-white"
            style={{ background: nodeColors[tooltip.node.node_type] }}
          >
            {tooltip.node.node_type.toUpperCase()}
          </span>
        </div>
      )}

      <svg
        className="w-full"
        style={{ height: height * zoom }}
        viewBox={`0 0 ${width} ${height}`}
        preserveAspectRatio="xMidYMid meet"
      >
        <defs>
          <filter height="160%" id="graphShadow" width="160%" x="-30%" y="-30%">
            <feDropShadow dx="0" dy="6" floodColor="#0f172a" floodOpacity="0.18" stdDeviation="6" />
          </filter>
          <filter id="focusPulse" width="200%" height="200%" x="-50%" y="-50%">
            <feGaussianBlur in="SourceGraphic" stdDeviation="6" />
          </filter>
        </defs>

        {/* Edges */}
        {edges.map((edge, i) => {
          const src = posMap.get(edge.source);
          const tgt = posMap.get(edge.target);
          if (!src || !tgt) return null;
          const isHighlighted = hoveredNodeId
            ? connectedIds.has(edge.source) && connectedIds.has(edge.target)
            : true;
          const color = edgeColors[edge.edge_type] || "#94a3b8";
          return (
            <g key={`e-${i}`}>
              <path
                d={curvedPath(src.x, src.y, tgt.x, tgt.y)}
                fill="none"
                stroke={edge.decision === "REJECTED" ? "#ef4444" : color}
                strokeDasharray={edge.edge_type === "review_task" ? "6 4" : undefined}
                strokeOpacity={isHighlighted ? 0.85 : 0.18}
                strokeWidth={edge.confidence ? Math.max(1.8, edge.confidence * 4) : 2}
              />
              {edge.confidence && isHighlighted ? (
                <text
                  fill="#475569"
                  fontSize="10"
                  fontWeight="600"
                  textAnchor="middle"
                  x={(src.x + tgt.x) / 2}
                  y={(src.y + tgt.y) / 2 - 8}
                >
                  {Math.round(edge.confidence * 100)}%
                </text>
              ) : null}
            </g>
          );
        })}

        {/* Nodes */}
        {simNodes.map((sn) => {
          const isFocus = sn.node.emphasis === "focus";
          const isHighlighted = hoveredNodeId ? connectedIds.has(sn.id) : true;
          const color = nodeColors[sn.node.node_type];
          return (
            <g
              key={sn.id}
              transform={`translate(${sn.x}, ${sn.y})`}
              style={{ cursor: "pointer", transition: "opacity 0.2s" }}
              opacity={isHighlighted ? 1 : 0.25}
              onMouseEnter={(e) => handleNodeHover(sn, e)}
              onMouseLeave={() => handleNodeHover(null)}
            >
              {/* Focus pulse ring */}
              {isFocus && (
                <circle
                  cx="0"
                  cy="0"
                  r={sn.radius + 16}
                  fill={color}
                  opacity="0.12"
                  filter="url(#focusPulse)"
                >
                  <animate
                    attributeName="r"
                    dur="2s"
                    repeatCount="indefinite"
                    values={`${sn.radius + 12};${sn.radius + 22};${sn.radius + 12}`}
                  />
                  <animate
                    attributeName="opacity"
                    dur="2s"
                    repeatCount="indefinite"
                    values="0.15;0.05;0.15"
                  />
                </circle>
              )}
              {/* Outer glow ring */}
              <circle
                cx="0"
                cy="0"
                r={sn.radius + 8}
                fill="none"
                stroke={color}
                strokeWidth="6"
                opacity={isFocus ? 0.28 : 0.14}
              />
              {/* Main circle */}
              <circle
                cx="0"
                cy="0"
                r={sn.radius}
                fill={color}
                filter="url(#graphShadow)"
                opacity="0.96"
              />
              {/* Inner icon text */}
              <text
                fill="#fff"
                fontSize={sn.node.node_type === "business" ? "13" : "11"}
                fontWeight="700"
                textAnchor="middle"
                y="4"
              >
                {sn.node.node_type === "business"
                  ? "UB"
                  : sn.node.node_type === "record"
                    ? "SR"
                    : sn.node.node_type === "activity"
                      ? "EV"
                      : "RV"}
              </text>
              {/* Label */}
              <text
                fill="#0f172a"
                fontSize="11"
                fontWeight="700"
                textAnchor="middle"
                y={sn.radius + 20}
              >
                {sn.node.label.length > 22
                  ? `${sn.node.label.slice(0, 20)}…`
                  : sn.node.label}
              </text>
              {/* Subtitle */}
              {sn.node.subtitle && (
                <text
                  fill="#64748b"
                  fontSize="10"
                  textAnchor="middle"
                  y={sn.radius + 34}
                >
                  {sn.node.subtitle.length > 28
                    ? `${sn.node.subtitle.slice(0, 25)}…`
                    : sn.node.subtitle}
                </text>
              )}
            </g>
          );
        })}
      </svg>
    </div>
  );
}
