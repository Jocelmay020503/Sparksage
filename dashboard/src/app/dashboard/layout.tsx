"use client";

import { SessionProvider } from "next-auth/react";
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/sidebar/app-sidebar";
import { Separator } from "@/components/ui/separator";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <SessionProvider>
      <SidebarProvider>
        <AppSidebar />
        <main className="flex-1 w-full overflow-x-hidden">
          <header className="flex h-14 items-center gap-2 border-b px-4 sticky top-0 bg-background z-10">
            <SidebarTrigger />
            <Separator orientation="vertical" className="h-6" />
            <span className="text-sm font-medium text-muted-foreground truncate">
              SparkSage Dashboard
            </span>
          </header>
          <div className="p-4 sm:p-6">{children}</div>
        </main>
      </SidebarProvider>
    </SessionProvider>
  );
}
