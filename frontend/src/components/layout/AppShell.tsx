"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { PropsWithChildren } from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

const nav = [
  { href: "/", label: "Dashboard" },
  { href: "/watchers", label: "Watchers" },
  { href: "/record", label: "Record Now" },
  { href: "/jobs", label: "Jobs" },
  { href: "/files", label: "Files" },
  { href: "/settings", label: "Settings" },
];

export default function AppShell({ children }: PropsWithChildren) {
  const pathname = usePathname();

  return (
    <div className="min-h-screen grid grid-cols-[240px_1fr]">
      <Card className="rounded-none border-t-0 border-l-0 border-b-0">
        <div className="p-4">
          <div className="font-semibold text-lg mb-4">TikTok Live Recorder</div>
          <nav className="flex flex-col gap-1">
            {nav.map((n) => (
              <Button
                key={n.href}
                asChild
                variant={pathname === n.href ? "default" : "ghost"}
                className="justify-start"
              >
                <Link href={n.href}>{n.label}</Link>
              </Button>
            ))}
          </nav>
        </div>
      </Card>
      <main className="p-6">
        <div className="container max-w-none">{children}</div>
      </main>
    </div>
  );
}
