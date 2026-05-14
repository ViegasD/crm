import { cn } from "@/lib/utils";

interface AvatarProps {
  name?: string;
  src?: string;
  size?: "sm" | "md" | "lg";
  className?: string;
}

const sizeMap = { sm: "h-7 w-7 text-xs", md: "h-9 w-9 text-sm", lg: "h-11 w-11 text-base" };

function initials(name?: string) {
  if (!name) return "?";
  return name
    .split(" ")
    .slice(0, 2)
    .map((n) => n[0])
    .join("")
    .toUpperCase();
}

const colors = [
  "bg-blue-500","bg-violet-500","bg-emerald-500","bg-amber-500","bg-rose-500","bg-sky-500",
];

function colorFor(name?: string) {
  if (!name) return colors[0];
  const code = name.charCodeAt(0) % colors.length;
  return colors[code];
}

export function Avatar({ name, src, size = "md", className }: AvatarProps) {
  return (
    <span
      className={cn(
        "inline-flex shrink-0 items-center justify-center rounded-full font-semibold text-white select-none",
        sizeMap[size],
        !src && colorFor(name),
        className
      )}
    >
      {src ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={src} alt={name} className="h-full w-full rounded-full object-cover" />
      ) : (
        initials(name)
      )}
    </span>
  );
}
