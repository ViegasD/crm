"use client";
import { useState } from "react";
import { ChannelsTab } from "@/components/settings/channels-tab";
import { TeamTab } from "@/components/settings/team-tab";
import { SectorsTab } from "@/components/settings/sectors-tab";
import { SlaTab } from "@/components/settings/sla-tab";
import { CannedResponsesTab } from "@/components/settings/canned-responses-tab";
import { LabelsTab } from "@/components/settings/labels-tab";
import { cn } from "@/lib/utils";

const TABS = ["Channels", "Team", "Sectors", "Labels", "Canned responses", "SLA"] as const;
type Tab = typeof TABS[number];

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<Tab>("Channels");

  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-border bg-white px-6 py-3">
        <h1 className="text-base font-semibold text-slate-900 mb-3">Settings</h1>
        <div className="flex gap-4">
          {TABS.map((t) => (
            <button
              key={t}
              onClick={() => setActiveTab(t)}
              className={cn(
                "pb-2 text-sm font-medium border-b-2 transition-colors",
                activeTab === t
                  ? "border-primary text-primary"
                  : "border-transparent text-muted hover:text-slate-700"
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
        {activeTab === "SLA" && <SlaTab />}
      </div>
    </div>
  );
}
