"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  MessageSquare, Users, Settings, GitBranch,
  BarChart2, LogOut,
} from "lucide-react";
import { useAuthStore } from "@/stores/auth-store";
import { Avatar } from "@/components/ui/avatar";
import { useRouter } from "next/navigation";

const navItems = [
  { href: "/inbox", icon: MessageSquare, label: "Inbox" },
  { href: "/contacts", icon: Users, label: "Contacts" },
  { href: "/flows", icon: GitBranch, label: "Flows" },
  { href: "/reports", icon: BarChart2, label: "Reports" },
  { href: "/settings", icon: Settings, label: "Settings" },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user, currentWorkspace, logout } = useAuthStore();
  const router = useRouter();

  function handleLogout() {
    logout();
    router.push("/login");
  }

  return (
    <aside className="flex h-screen w-14 flex-col items-center bg-sidebar py-3 shrink-0">
      {/* Workspace avatar */}
      <div
        className="mb-4 flex h-9 w-9 items-center justify-center rounded-lg bg-primary text-white text-sm font-bold hover:opacity-90"
        title={currentWorkspace?.name}
      >
        {currentWorkspace?.name?.[0]?.toUpperCase() ?? "W"}
      </div>

      {/* Nav */}
      <nav className="flex flex-1 flex-col items-center gap-1">
        {navItems.map(({ href, icon: Icon, label }) => {
          const active = pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex h-10 w-10 items-center justify-center rounded-lg transition-colors",
                active
                  ? "bg-primary text-white"
                  : "text-sidebar-text hover:bg-sidebar-hover hover:text-white"
              )}
              title={label}
            >
              <Icon className="h-5 w-5" />
            </Link>
          );
        })}
      </nav>

      {/* User avatar + logout */}
      <div className="flex flex-col items-center gap-2 mt-2">
        <Avatar name={user?.name} src={user?.avatarUrl} size="sm" className="cursor-pointer" />
        <button
          onClick={handleLogout}
          className="text-sidebar-text hover:text-white"
          title="Logout"
        >
          <LogOut className="h-4 w-4" />
        </button>
      </div>
    </aside>
  );
}
