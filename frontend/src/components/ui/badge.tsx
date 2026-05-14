import { cn } from "@/lib/utils";
import type { ConversationStatus } from "@/types/conversation";

interface BadgeProps {
  children: React.ReactNode;
  className?: string;
  variant?: "default" | "status" | "dot";
  status?: ConversationStatus | "ok" | "at_risk" | "violated";
}

const statusColors: Record<string, string> = {
  open: "bg-blue-100 text-blue-700",
  in_progress: "bg-amber-100 text-amber-700",
  resolved: "bg-green-100 text-green-700",
  pending: "bg-purple-100 text-purple-700",
  ok: "bg-green-100 text-green-700",
  at_risk: "bg-amber-100 text-amber-700",
  violated: "bg-red-100 text-red-700",
};

const statusDots: Record<string, string> = {
  open: "bg-blue-500",
  in_progress: "bg-amber-500",
  resolved: "bg-green-500",
  pending: "bg-purple-500",
};

export function Badge({ children, className, status }: BadgeProps) {
  const color = status ? statusColors[status] : "bg-slate-100 text-slate-600";
  return (
    <span className={cn("inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium", color, className)}>
      {status && statusDots[status] && (
        <span className={cn("h-1.5 w-1.5 rounded-full", statusDots[status])} />
      )}
      {children}
    </span>
  );
}
