"use client";
import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/auth-store";
import { flowsApi } from "@/lib/api";
import type { Flow, FlowGraph, FlowNode, FlowEdge } from "@/types/flow";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Save, Plus } from "lucide-react";
import {
  ReactFlow,
  addEdge,
  Background,
  Controls,
  MiniMap,
  useEdgesState,
  useNodesState,
  type Connection,
  type Node,
  type Edge,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

const NODE_TYPES_LIST = [
  { type: "trigger", label: "Trigger", color: "bg-purple-100 border-purple-400" },
  { type: "message", label: "Message", color: "bg-blue-100 border-blue-400" },
  { type: "menu", label: "Menu", color: "bg-yellow-100 border-yellow-400" },
  { type: "condition", label: "Condition", color: "bg-orange-100 border-orange-400" },
  { type: "assign_agent", label: "Assign Agent", color: "bg-green-100 border-green-400" },
  { type: "end", label: "End", color: "bg-red-100 border-red-400" },
];

function toRFNodes(nodes: FlowNode[]): Node[] {
  return nodes.map((n) => ({
    id: n.id,
    type: "default",
    position: n.position,
    data: { label: n.label ?? n.type, flowType: n.type, parameters: n.parameters },
  }));
}

function toRFEdges(edges: FlowEdge[]): Edge[] {
  return edges.map((e) => ({
    id: e.id,
    source: e.source,
    sourceHandle: e.sourceHandle,
    target: e.target,
    targetHandle: e.targetHandle,
  }));
}

function fromRF(rfNodes: Node[], rfEdges: Edge[]): FlowGraph {
  return {
    version: 1,
    nodes: rfNodes.map((n) => ({
      id: n.id,
      type: (n.data.flowType as FlowNode["type"]) ?? "message",
      position: n.position,
      parameters: (n.data.parameters as Record<string, unknown>) ?? {},
      label: n.data.label as string,
    })),
    edges: rfEdges.map((e) => ({
      id: e.id,
      source: e.source,
      sourceHandle: e.sourceHandle ?? "default",
      target: e.target,
      targetHandle: e.targetHandle ?? undefined,
    })),
  };
}

let nodeCounter = 100;

export default function FlowEditorPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const { currentWorkspace } = useAuthStore();
  const [flow, setFlow] = useState<Flow | null>(null);
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!currentWorkspace || !params.id) return;
    flowsApi.get(currentWorkspace.id, params.id).then((r) => {
      const f = r.data as Flow;
      setFlow(f);
      if (f.graph) {
        setNodes(toRFNodes(f.graph.nodes));
        setEdges(toRFEdges(f.graph.edges));
      }
    });
  }, [currentWorkspace?.id, params.id]); // eslint-disable-line react-hooks/exhaustive-deps

  const onConnect = useCallback((conn: Connection) => {
    setEdges((eds) => addEdge(conn, eds));
  }, [setEdges]);

  async function save() {
    if (!currentWorkspace || !flow) return;
    setSaving(true);
    try {
      await flowsApi.update(currentWorkspace.id, flow.id, { graph: fromRF(nodes, edges) });
    } finally {
      setSaving(false);
    }
  }

  function addNode(type: string, label: string) {
    const id = `node_${++nodeCounter}`;
    setNodes((prev) => [
      ...prev,
      {
        id,
        type: "default",
        position: { x: 200 + Math.random() * 200, y: 100 + Math.random() * 200 },
        data: { label, flowType: type, parameters: {} },
      },
    ]);
  }

  return (
    <div className="flex h-full flex-col">
      {/* Toolbar */}
      <div className="flex items-center justify-between border-b border-border bg-white px-4 py-2 shrink-0">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="sm" onClick={() => router.push("/flows")}>
            <ArrowLeft className="h-4 w-4" /> Back
          </Button>
          <span className="font-semibold text-slate-900">{flow?.name ?? "Loading…"}</span>
          {flow?.isActive && (
            <span className="rounded-full bg-green-100 px-2 py-0.5 text-[10px] font-bold text-green-700">ACTIVE</span>
          )}
        </div>
        <Button size="sm" loading={saving} onClick={save}>
          <Save className="h-3.5 w-3.5" /> Save
        </Button>
      </div>

      <div className="flex flex-1 min-h-0">
        {/* Node palette */}
        <div className="w-44 shrink-0 border-r border-border bg-white flex flex-col gap-1 p-3 overflow-y-auto">
          <p className="text-[10px] font-bold uppercase text-muted mb-1">Nodes</p>
          {NODE_TYPES_LIST.map((n) => (
            <button
              key={n.type}
              onClick={() => addNode(n.type, n.label)}
              className={`flex items-center gap-1.5 rounded-md border px-2 py-1.5 text-xs font-medium text-left transition-colors hover:opacity-80 ${n.color}`}
            >
              <Plus className="h-3 w-3 shrink-0" />
              {n.label}
            </button>
          ))}
        </div>

        {/* Canvas */}
        <div className="flex-1">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            fitView
          >
            <Background />
            <Controls />
            <MiniMap />
          </ReactFlow>
        </div>
      </div>
    </div>
  );
}
