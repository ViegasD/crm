import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const PROTECTED = ["/inbox", "/contacts", "/flows", "/settings", "/reports"];
const PUBLIC = ["/login", "/register"];

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;

  const isProtected = PROTECTED.some((p) => pathname.startsWith(p));
  const isPublic = PUBLIC.some((p) => pathname.startsWith(p));

  // Zustand persists to localStorage — not accessible in middleware.
  // Use a cookie set at login time for SSR route protection.
  const token = request.cookies.get("access_token")?.value;

  if (isProtected && !token) {
    const url = request.nextUrl.clone();
    url.pathname = "/login";
    return NextResponse.redirect(url);
  }

  if (isPublic && token) {
    const url = request.nextUrl.clone();
    url.pathname = "/inbox";
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/inbox/:path*", "/contacts/:path*", "/flows/:path*", "/settings/:path*", "/reports/:path*", "/login", "/register"],
};
