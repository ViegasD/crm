"use client";
import { useEffect, useState } from "react";
import { useAuthStore } from "@/stores/auth-store";
import { contactsApi } from "@/lib/api";
import type { Contact } from "@/types/contact";
import { Input, Label, Select } from "@/components/ui/form";
import { Button } from "@/components/ui/button";
import { Avatar } from "@/components/ui/avatar";
import { Modal } from "@/components/ui/modal";
import { Plus, Search, Trash2 } from "lucide-react";

export default function ContactsPage() {
  const { currentWorkspace } = useAuthStore();
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [createOpen, setCreateOpen] = useState(false);
  const pageSize = 30;

  useEffect(() => {
    if (!currentWorkspace) return;
    setLoading(true);
    contactsApi
      .list(currentWorkspace.id, { search: search || undefined, page, page_size: pageSize })
      .then((r) => {
        setContacts(r.data.items ?? []);
        setTotal(r.data.total ?? 0);
      })
      .finally(() => setLoading(false));
  }, [currentWorkspace?.id, search, page]); // eslint-disable-line react-hooks/exhaustive-deps

  async function deleteContact(id: string) {
    if (!currentWorkspace) return;
    if (!confirm("Delete this contact?")) return;
    await contactsApi.delete(currentWorkspace.id, id);
    setContacts((prev) => prev.filter((c) => c.id !== id));
  }

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="flex h-full flex-col">
      {/* Toolbar */}
      <div className="flex items-center justify-between border-b border-border bg-white px-6 py-3">
        <h1 className="text-base font-semibold text-slate-900">Contacts</h1>
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted" />
            <input
              placeholder="Search contacts…"
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1); }}
              className="h-8 rounded-md border border-border pl-8 pr-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
          <Button size="sm" onClick={() => setCreateOpen(true)}>
            <Plus className="h-3.5 w-3.5" /> Add contact
          </Button>
        </div>
      </div>

      {/* Table */}
      <div className="flex-1 overflow-y-auto">
        <table className="w-full text-sm">
          <thead className="sticky top-0 bg-surface-2 border-b border-border">
            <tr>
              <th className="px-4 py-2.5 text-left font-medium text-muted">Name</th>
              <th className="px-4 py-2.5 text-left font-medium text-muted">Type</th>
              <th className="px-4 py-2.5 text-left font-medium text-muted">Phone</th>
              <th className="px-4 py-2.5 text-left font-medium text-muted">Email</th>
              <th className="px-4 py-2.5 text-left font-medium text-muted">Status</th>
              <th className="px-4 py-2.5" />
            </tr>
          </thead>
          <tbody className="divide-y divide-border bg-white">
            {loading && (
              <tr><td colSpan={6} className="py-8 text-center text-muted">Loading…</td></tr>
            )}
            {!loading && contacts.length === 0 && (
              <tr><td colSpan={6} className="py-8 text-center text-muted">No contacts found</td></tr>
            )}
            {contacts.map((c) => (
              <tr key={c.id} className="hover:bg-surface-2">
                <td className="px-4 py-2.5">
                  <div className="flex items-center gap-2">
                    <Avatar name={c.name} size="sm" />
                    <span className="font-medium text-slate-900">{c.name}</span>
                    {c.isPriority && <span className="text-[10px] font-bold text-amber-500 uppercase">Priority</span>}
                  </div>
                </td>
                <td className="px-4 py-2.5 text-slate-500 capitalize">{c.type}</td>
                <td className="px-4 py-2.5 text-slate-500">{c.phones?.[0]?.phone ?? "—"}</td>
                <td className="px-4 py-2.5 text-slate-500">{c.emails?.[0]?.email ?? "—"}</td>
                <td className="px-4 py-2.5">
                  <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium
                    ${c.status === "active" ? "bg-green-100 text-green-700" :
                      c.status === "blocked" ? "bg-red-100 text-red-700" : "bg-slate-100 text-slate-600"}`}>
                    {c.status}
                  </span>
                </td>
                <td className="px-4 py-2.5">
                  <button onClick={() => deleteContact(c.id)} className="text-muted hover:text-danger transition-colors">
                    <Trash2 className="h-4 w-4" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between border-t border-border bg-white px-6 py-2">
          <span className="text-sm text-muted">{total} contacts · page {page} of {totalPages}</span>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>Previous</Button>
            <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>Next</Button>
          </div>
        </div>
      )}

      <CreateContactModal
        open={createOpen}
        workspaceId={currentWorkspace?.id ?? ""}
        onClose={() => setCreateOpen(false)}
        onCreated={(c) => setContacts((prev) => [c, ...prev])}
      />
    </div>
  );
}

function CreateContactModal({ open, onClose, workspaceId, onCreated }: {
  open: boolean; onClose: () => void; workspaceId: string; onCreated: (c: Contact) => void;
}) {
  const [name, setName] = useState("");
  const [type, setType] = useState("customer");
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name) { setError("Name is required"); return; }
    setLoading(true);
    try {
      const r = await contactsApi.create(workspaceId, {
        name, type,
        phones: phone ? [{ phone, is_primary: true }] : [],
        emails: email ? [{ email, is_primary: true }] : [],
      });
      onCreated(r.data as Contact);
      onClose();
      setName(""); setPhone(""); setEmail(""); setType("customer"); setError("");
    } catch {
      setError("Failed to create contact");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Modal open={open} onClose={onClose} title="New Contact">
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div className="flex flex-col gap-1.5">
          <Label>Name *</Label>
          <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Full name" />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label>Type</Label>
          <Select value={type} onChange={(e) => setType(e.target.value)}>
            <option value="customer">Customer</option>
            <option value="lead">Lead</option>
            <option value="partner">Partner</option>
            <option value="other">Other</option>
          </Select>
        </div>
        <div className="flex flex-col gap-1.5">
          <Label>Phone</Label>
          <Input value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="+55 11 99999-9999" />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label>Email</Label>
          <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="name@company.com" />
        </div>
        {error && <p className="text-sm text-danger">{error}</p>}
        <div className="flex gap-2 justify-end">
          <Button variant="outline" type="button" onClick={onClose}>Cancel</Button>
          <Button type="submit" loading={loading}>Create</Button>
        </div>
      </form>
    </Modal>
  );
}

