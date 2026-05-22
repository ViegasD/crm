"use client";
import { useState } from "react";
import { ChannelsTab } from "@/components/settings/channels-tab";
import { TeamTab } from "@/components/settings/team-tab";
import { SectorsTab } from "@/components/settings/sectors-tab";
import { SlaTab } from "@/components/settings/sla-tab";
import { CannedResponsesTab } from "@/components/settings/canned-responses-tab";
import { LabelsTab } from "@/components/settings/labels-tab";
import { MacrosTab } from "@/components/settings/macros-tab";
import { ReasonsTab } from "@/components/settings/reasons-tab";
import { WebhookEventsTab } from "@/components/settings/webhook-events-tab";
import { WebhookOpsTab } from "@/components/settings/webhook-ops-tab";
import { cn } from "@/lib/utils";

const TABS = [
  "Channels",
  "Team",
  "Sectors",
  "Labels",
  "Canned responses",
  "Macros",
  "Reasons",
  "SLA",
  "Webhooks",
  "Webhook ops",
] as const;
type Tab = typeof TABS[number];

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<Tab>("Channels");

  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-border bg-white px-6 py-3">
        <h1 className="mb-3 text-base font-semibold text-slate-900">Settings</h1>
        <div className="flex flex-wrap gap-4">
          {TABS.map((t) => (
            <button
              key={t}
              onClick={() => setActiveTab(t)}
              className={cn(
                "border-b-2 pb-2 text-sm font-medium transition-colors",
                activeTab === t
                  ? "border-primary text-primary"
                  : "border-transparent text-muted hover:text-slate-700",
              )}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-6 py-6">
        {activeTab === "Channels" && <ChannelsTab />}
        {activeTab === "Team" && <TeamTab />}
        {activeTab === "Sectors" && <SectorsTab />}
        {activeTab === "Labels" && <LabelsTab />}
        {activeTab === "Canned responses" && <CannedResponsesTab />}
        {activeTab === "Macros" && <MacrosTab />}
        {activeTab === "Reasons" && <ReasonsTab />}
        {activeTab === "SLA" && <SlaTab />}
        {activeTab === "Webhooks" && <WebhookEventsTab />}
        {activeTab === "Webhook ops" && <WebhookOpsTab />}
      </div>
    </div>
  );
}
