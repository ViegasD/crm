export type ContactType = "customer" | "lead" | "partner" | "supplier" | "other";
export type ContactStatus = "active" | "inactive" | "blocked";

export interface ContactPhone {
  phone: string;
  label?: string;
  isPrimary: boolean;
}

export interface ContactEmail {
  email: string;
  label?: string;
  isPrimary: boolean;
}

export interface Contact {
  id: string;
  workspaceId: string;
  name: string;
  type: ContactType;
  status: ContactStatus;
  document?: string;
  company?: string;
  avatarUrl?: string;
  isPriority: boolean;
  phones: ContactPhone[];
  emails: ContactEmail[];
  createdAt: string;
}

export interface ContactCreate {
  name: string;
  type: ContactType;
  document?: string;
  company?: string;
  phones: ContactPhone[];
  emails: ContactEmail[];
}
