// Flow builder TypeScript types mirroring FlowGraph/FlowNode/FlowEdge models

export type FlowNodeType =
  | "trigger" | "message" | "bot" | "question" | "input_validated"
  | "menu" | "condition" | "switch" | "set_variable" | "action"
  | "http_request" | "wait" | "subflow" | "assign_agent"
  | "tag" | "note" | "end";

export interface FlowNode {
  id: string;
  type: FlowNodeType;
  position: { x: number; y: number };
  parameters: Record<string, unknown>;
  label?: string;
}

export interface FlowEdge {
  id: string;
  source: string;
  sourceHandle: string;
  target: string;
  targetHandle?: string;
}

export interface FlowGraph {
  version: number;
  nodes: FlowNode[];
  edges: FlowEdge[];
}
