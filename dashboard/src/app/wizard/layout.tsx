import Link from "next/link";
import { Zap } from "lucide-react";
import { redirect } from "next/navigation";
import { auth } from "@/lib/auth";

export default async function WizardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const session = await auth();
  const token = (session as { accessToken?: string } | null)?.accessToken;

  // Enforce login at the route level in case middleware is skipped by platform config.
  if (!session || !token) {
    redirect("/login?callbackUrl=/wizard");
  }

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b">
        <div className="mx-auto flex h-14 max-w-3xl items-center justify-between px-4">
          <div className="flex items-center gap-2 font-semibold">
            <Zap className="h-5 w-5" />
            SparkSage Setup
          </div>
          <Link
            href="/dashboard"
            className="text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            Skip setup
          </Link>
        </div>
      </header>
      <main className="mx-auto max-w-3xl px-4 py-8">{children}</main>
    </div>
  );
}
