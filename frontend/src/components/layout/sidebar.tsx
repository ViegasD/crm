"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";
import { AtSign, BarChart2, GitBranch, LogOut, MessageSquare, Settings, Users } from "lucide-react";
import { useAuthStore } from "@/stores/auth-store";
import { Avatar } from "@/components/ui/avatar";
import { useRouter } from "next/navigation";
import { mentionsApi } from "@/lib/api";

const navItems = [
  { href: "/inbox", icon: MessageSquare, label: "Inbox" },
  { href: "/mentions", icon: AtSign, label: "Mentions" },
  { href: "/contacts", icon: Users, label: "Contacts" },
  { href: "/flows", icon: GitBranch, label: "Flows" },
  { href: "/reports", icon: BarChart2, label: "Reports" },
  { href: "/settings", icon: Settings, label: "Settings" },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user, currentWorkspace, logout } = useAuthStore();
  const router = useRouter();
  const [unreadMentions, setUnreadMentions] = useState(0);

  useEffect(() => {
    if (!currentWorkspace) return;
    let timer: number | undefined;
    const refresh = () => {
      mentionsApi
        .list(currentWorkspace.id, { unread: true, page_size: 1 })
        .then((r) => setUnreadMentions(r.data?.unreadCount ?? 0))
        .catch(() => undefined);
    };
    refresh();
    timer = window.setInterval(refresh, 60_000);
    return () => {
      if (timer) window.clearInterval(timer);
    };
  }, [currentWorkspace?.id]);

  function handleLogout() {
    logout();
    router.push("/login");
  }

  return (
    <aside className="flex h-screen w-14 shrink-0 flex-col items-center bg-sidebar py-3">
      <div
        className="mb-4 flex h-9 w-9 items-center justify-center rounded-lg bg-primary text-sm font-bold text-white hover:opacity-90"
        title={currentWorkspace?.name}
      >
        {currentWorkspace?.name?.[0]?.toUpperCase() ?? "W"}
      </div>

      <nav className="flex flex-1 flex-col items-center gap-1">
        {navItems.map(({ href, icon: Icon, label }) => {
          const active = pathname.startsWith(href);
          const badge = href === "/mentions" && unreadMentions > 0;
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "relative flex h-10 w-10 items-center justify-center rounded-lg transition-colors",
                active
                  ? "bg-primary text-white"
                  : "text-sidebar-text hover:bg-sidebar-hover hover:text-white",
              )}
              title={label}
            >
              <Icon className="h-5 w-5" />
              {badge && (
                <span className="absolute -right-0.5 -top-0.5 inline-flex h-4 min-w-[1rem] items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-bold text-white">
                  {unreadMentions > 9 ? "9+" : unreadMentions}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      <div className="mt-2 flex flex-col items-center gap-2">
        <Avatar name={user?.name} src={user?.avatarUrl} size="sm" className="cursor-pointer" />
        <button onClick={handleLogout} className="text-sidebar-text hover:text-white" title="Logout">
          <LogOut className="h-4 w-4" />
        </button>
      </div>
    </aside>
  );
}
