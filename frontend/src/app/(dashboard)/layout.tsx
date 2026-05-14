export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <aside className="w-16 shrink-0" />
      {/* Main */}
      <main className="flex-1 overflow-hidden">{children}</main>
    </div>
  );
}
