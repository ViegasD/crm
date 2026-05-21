"use client";
import { useEffect, useState } from "react";
import { useAuthStore } from "@/stores/auth-store";
import { channelsApi } from "@/lib/api";
import type { ChannelAccount } from "@/types/channel";
import { Button } from "@/components/ui/button";
import { Modal } from "@/components/ui/modal";
import { Input, Label, Select } from "@/components/ui/form";
import { Plus, Trash2, Wifi, WifiOff } from "lucide-react";

const STATUS_COLORS: Record<string, string> = {
  active: "bg-green-100 text-green-700",
  inactive: "bg-slate-100 text-slate-600",
  error: "bg-red-100 text-red-700",
  pending: "bg-yellow-100 text-yellow-700",
} as const;

export function ChannelsTab() {
  const { currentWorkspace } = useAuthStore();
  const [channels, setChannels] = useState<ChannelAccount[]>([]);
  const [loading, setLoading] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);

  useEffect(() => {
    if (!currentWorkspace) return;
    setLoading(true);
    channelsApi.list(currentWorkspace.id)
      .then((r) => setChannels(r.data ?? []))
      .finally(() => setLoading(false));
  }, [currentWorkspace?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  async function deleteChannel(id: string) {
    if (!currentWorkspace) return;
    if (!confirm("Remove this channel?")) return;
    await channelsApi.delete(currentWorkspace.id, id);
    setChannels((prev) => prev.filter((c) => c.id !== id));
  }

  return (
    <div className="max-w-2xl">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="font-semibold text-slate-900">Channel Accounts</h2>
          <p className="text-sm text-muted">Connect WhatsApp and other messaging channels</p>
        </div>
        <Button size="sm" onClick={() => setCreateOpen(true)}>
          <Plus className="h-3.5 w-3.5" /> Add channel
        </Button>
      </div>

      {loading && <p className="text-sm text-muted">Loading…</p>}
      <div className="flex flex-col gap-3">
        {channels.map((ch) => (
          <div key={ch.id} className="flex items-center justify-between rounded-lg border border-border bg-white p-4">
            <div className="flex items-center gap-3">
              {ch.status === "active" ? (
                <Wifi className="h-5 w-5 text-green-500" />
              ) : (
                <WifiOff className="h-5 w-5 text-slate-400" />
              )}
              <div>
              <p className="font-medium text-slate-900">{ch.displayName}</p>
                <p className="text-xs text-muted capitalize">{ch.channelType} · {ch.provider}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_COLORS[ch.status ?? "inactive"] ?? STATUS_COLORS.inactive}`}>
                {ch.status}
              </span>
              <button onClick={() => deleteChannel(ch.id)} className="text-muted hover:text-danger">
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          </div>
        ))}
        {!loading && channels.length === 0 && (
          <div className="rounded-lg border border-dashed border-border p-8 text-center text-sm text-muted">
            No channels connected yet. Add one to start receiving messages.
          </div>
        )}
      </div>

      <CreateChannelModal
        open={createOpen}
        workspaceId={currentWorkspace?.id ?? ""}
        onClose={() => setCreateOpen(false)}
        onCreated={(c) => setChannels((prev) => [...prev, c])}
      />
    </div>
  );
}

function CreateChannelModal({ open, onClose, workspaceId, onCreated }: {
  open: boolean; onClose: () => void; workspaceId: string; onCreated: (c: ChannelAccount) => void;
}) {
  const [name, setName] = useState("");
  const [channelType, setChannelType] = useState("whatsapp");
  const [provider, setProvider] = useState("evolution_baileys");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  // Evolution fields
  const [evoUrl, setEvoUrl] = useState("");
  const [evoKey, setEvoKey] = useState("");
  const [evoInstance, setEvoInstance] = useState("");
  const [evoWebhookSecret, setEvoWebhookSecret] = useState("");
  // Meta Cloud fields
  const [metaToken, setMetaToken] = useState("");
  const [metaAppSecret, setMetaAppSecret] = useState("");
  const [metaPhoneId, setMetaPhoneId] = useState("");
  const [metaWabaId, setMetaWabaId] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name) { setError("Name required"); return; }
    setLoading(true);
    try {
      const r = await channelsApi.create(workspaceId, {
        display_name: name,
        channel_type: channelType,
        provider,
        phone_number_id: provider === "meta_cloud" ? metaPhoneId : undefined,
        waba_id: provider === "meta_cloud" ? metaWabaId : undefined,
        external_account_id: provider.startsWith("evolution") ? evoInstance : undefined,
      });
      const ch = r.data as ChannelAccount;
      // Upsert credentials
      const creds = provider.startsWith("evolution")
        ? {
            evolution_base_url: evoUrl,
            evolution_api_key: evoKey,
            evolution_instance_id: evoInstance,
            webhook_secret: evoWebhookSecret,
          }
        : { access_token: metaToken, app_secret: metaAppSecret };
      await channelsApi.upsertCredential(workspaceId, ch.id, provider.startsWith("evolution") ? "evolution" : "meta_cloud", creds);
      onCreated(ch);
      onClose();
      setName(""); setEvoUrl(""); setEvoKey(""); setEvoInstance(""); setEvoWebhookSecret("");
      setMetaToken(""); setMetaAppSecret(""); setMetaPhoneId(""); setMetaWabaId(""); setError("");
    } catch {
      setError("Failed to create channel");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Modal open={open} onClose={onClose} title="Add Channel" size="md">
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div className="flex flex-col gap-1.5">
          <Label>Name *</Label>
          <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Sales WhatsApp" />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div className="flex flex-col gap-1.5">
            <Label>Channel</Label>
            <Select value={channelType} onChange={(e) => setChannelType(e.target.value)}>
              <option value="whatsapp">WhatsApp</option>
            </Select>
          </div>
          <div className="flex flex-col gap-1.5">
            <Label>Provider</Label>
            <Select value={provider} onChange={(e) => setProvider(e.target.value)}>
              <option value="evolution_baileys">Evolution API - Baileys</option>
              <option value="evolution_cloud">Evolution API - Cloud</option>
              <option value="meta_cloud">Meta Cloud API</option>
            </Select>
          </div>
        </div>

        {provider.startsWith("evolution") && (
          <>
            <div className="flex flex-col gap-1.5">
              <Label>Evolution URL</Label>
              <Input value={evoUrl} onChange={(e) => setEvoUrl(e.target.value)} placeholder="https://evo.yourserver.com" />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label>API Key</Label>
              <Input value={evoKey} onChange={(e) => setEvoKey(e.target.value)} placeholder="Global API key" />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label>Instance Name</Label>
              <Input value={evoInstance} onChange={(e) => setEvoInstance(e.target.value)} placeholder="my-instance" />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label>Webhook Secret</Label>
              <Input value={evoWebhookSecret} onChange={(e) => setEvoWebhookSecret(e.target.value)} placeholder="Shared HMAC secret" />
            </div>
          </>
        )}

        {provider === "meta_cloud" && (
          <>
            <div className="flex flex-col gap-1.5">
              <Label>Access Token</Label>
              <Input value={metaToken} onChange={(e) => setMetaToken(e.target.value)} placeholder="EAAxxxxxxx..." />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label>App Secret</Label>
              <Input value={metaAppSecret} onChange={(e) => setMetaAppSecret(e.target.value)} placeholder="Meta app secret" />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label>Phone Number ID</Label>
              <Input value={metaPhoneId} onChange={(e) => setMetaPhoneId(e.target.value)} placeholder="1234567890" />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label>WABA ID</Label>
              <Input value={metaWabaId} onChange={(e) => setMetaWabaId(e.target.value)} placeholder="9876543210" />
            </div>
          </>
        )}

        {error && <p className="text-sm text-danger">{error}</p>}
        <div className="flex gap-2 justify-end">
          <Button variant="outline" type="button" onClick={onClose}>Cancel</Button>
          <Button type="submit" loading={loading}>Add channel</Button>
        </div>
      </form>
    </Modal>
  );
}
