"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input, Label, Select } from "@/components/ui/form";
import { contactsApi } from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";
import type { Contact, ContactStatus } from "@/types/contact";

export default function ContactProfilePage() {
  const params = useParams<{ id: string }>();
  const contactId = Array.isArray(params?.id) ? params.id[0] : params?.id;
  const { currentWorkspace } = useAuthStore();

  const [contact, setContact] = useState<Contact | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [saveMessage, setSaveMessage] = useState("");

  const [name, setName] = useState("");
  const [status, setStatus] = useState<ContactStatus>("active");
  const [company, setCompany] = useState("");
  const [document, setDocument] = useState("");
  const [isPriority, setIsPriority] = useState(false);

  useEffect(() => {
    if (!currentWorkspace?.id || !contactId) return;
    setLoading(true);
    setError("");

    contactsApi.get(currentWorkspace.id, contactId)
      .then((response) => {
        const nextContact = response.data as Contact;
        setContact(nextContact);
        setName(nextContact.name ?? "");
        setStatus(nextContact.status ?? "active");
        setCompany(nextContact.company ?? "");
        setDocument(nextContact.document ?? "");
        setIsPriority(Boolean(nextContact.isPriority));
      })
      .catch(() => setError("Failed to load contact"))
      .finally(() => setLoading(false));
  }, [currentWorkspace?.id, contactId]);

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    if (!currentWorkspace?.id || !contactId) return;

    setSaving(true);
    setError("");
    setSaveMessage("");
    try {
      const response = await contactsApi.update(currentWorkspace.id, contactId, {
        name,
        status,
        company: company || null,
        document: document || null,
        is_priority: isPriority,
      });
      const updated = response.data as Contact;
      setContact(updated);
      setName(updated.name ?? "");
      setStatus(updated.status ?? "active");
      setCompany(updated.company ?? "");
      setDocument(updated.document ?? "");
      setIsPriority(Boolean(updated.isPriority));
      setSaveMessage("Contact updated")
    } catch {
      setError("Failed to update contact");
    } finally {
      setSaving(false);
    }
  }

  if (!currentWorkspace) {
    return <div className="p-6 text-sm text-muted">Workspace not loaded yet.</div>;
  }

  if (loading) {
    return <div className="p-6 text-sm text-muted">Loading contact...</div>;
  }

  if (!contact || !contactId) {
    return <div className="p-6 text-sm text-muted">Contact not found.</div>;
  }

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-6 p-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <Link href="/contacts" className="text-sm text-primary hover:underline">Back to contacts</Link>
          <h1 className="mt-2 text-2xl font-semibold text-slate-900">{contact.name}</h1>
          <p className="mt-1 text-sm text-muted">Contact profile and CRM details.</p>
        </div>
        <span className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wide ${
          contact.status === "active"
            ? "bg-green-100 text-green-700"
            : contact.status === "blocked"
              ? "bg-red-100 text-red-700"
              : "bg-slate-100 text-slate-600"
        }`}>
          {contact.status}
        </span>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.6fr_1fr]">
        <form onSubmit={handleSave} className="rounded-2xl border border-border bg-white p-6 shadow-sm">
          <h2 className="text-base font-semibold text-slate-900">Profile</h2>
          <div className="mt-5 grid gap-4 md:grid-cols-2">
            <div className="md:col-span-2 flex flex-col gap-1.5">
              <Label>Name</Label>
              <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Full name" />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label>Status</Label>
              <Select value={status} onChange={(e) => setStatus(e.target.value as ContactStatus)}>
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
                <option value="blocked">Blocked</option>
              </Select>
            </div>
            <div className="flex flex-col gap-1.5">
              <Label>Type</Label>
              <Input value={contact.type} disabled />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label>Company</Label>
              <Input value={company} onChange={(e) => setCompany(e.target.value)} placeholder="Company" />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label>Document</Label>
              <Input value={document} onChange={(e) => setDocument(e.target.value)} placeholder="Document or ID" />
            </div>
          </div>

          <label className="mt-5 flex items-center gap-3 rounded-xl border border-border px-4 py-3 text-sm text-slate-700">
            <input
              type="checkbox"
              checked={isPriority}
              onChange={(e) => setIsPriority(e.target.checked)}
              className="h-4 w-4 rounded border-border text-primary focus:ring-primary"
            />
            Mark as priority contact
          </label>

          {error && <p className="mt-4 text-sm text-danger">{error}</p>}
          {saveMessage && <p className="mt-4 text-sm text-green-700">{saveMessage}</p>}

          <div className="mt-6 flex justify-end">
            <Button type="submit" loading={saving}>Save changes</Button>
          </div>
        </form>

        <div className="flex flex-col gap-6">
          <section className="rounded-2xl border border-border bg-white p-6 shadow-sm">
            <h2 className="text-base font-semibold text-slate-900">Contact Methods</h2>
            <div className="mt-4 space-y-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-muted">Phones</p>
                <div className="mt-2 space-y-2">
                  {contact.phones?.length ? contact.phones.map((phone, index) => (
                    <div key={`${phone.phone}-${index}`} className="rounded-xl bg-surface-2 px-3 py-2 text-sm text-slate-700">
                      <p>{phone.phone}</p>
                      {phone.label && <p className="text-xs text-muted">{phone.label}</p>}
                    </div>
                  )) : <p className="text-sm text-muted">No phone numbers</p>}
                </div>
              </div>

              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-muted">Emails</p>
                <div className="mt-2 space-y-2">
                  {contact.emails?.length ? contact.emails.map((email, index) => (
                    <div key={`${email.email}-${index}`} className="rounded-xl bg-surface-2 px-3 py-2 text-sm text-slate-700">
                      <p>{email.email}</p>
                      {email.label && <p className="text-xs text-muted">{email.label}</p>}
                    </div>
                  )) : <p className="text-sm text-muted">No emails</p>}
                </div>
              </div>
            </div>
          </section>

          <section className="rounded-2xl border border-border bg-white p-6 shadow-sm">
            <h2 className="text-base font-semibold text-slate-900">CRM Metadata</h2>
            <dl className="mt-4 space-y-3 text-sm">
              <div className="flex items-start justify-between gap-4">
                <dt className="text-muted">Contact ID</dt>
                <dd className="break-all text-right text-slate-700">{contact.id}</dd>
              </div>
              <div className="flex items-start justify-between gap-4">
                <dt className="text-muted">Integration ID</dt>
                <dd className="break-all text-right text-slate-700">{contact.integrationId ?? "—"}</dd>
              </div>
              <div className="flex items-start justify-between gap-4">
                <dt className="text-muted">Created at</dt>
                <dd className="text-right text-slate-700">{new Date(contact.createdAt).toLocaleString()}</dd>
              </div>
            </dl>
          </section>
        </div>
      </div>
    </div>
  );
}