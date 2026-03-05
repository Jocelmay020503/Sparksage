"use client";

import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import { Loader2, ShieldAlert, User, Building2 } from "lucide-react";
import { api, RateLimitSummary } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function QuotaPage() {
  const { data: session } = useSession();
  const token = (session as { accessToken?: string })?.accessToken;

  const [data, setData] = useState<RateLimitSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    if (!token) return;
    try {
      setLoading(true);
      setError(null);
      const summary = await api.getRateLimitSummary(token);
      setData(summary);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load quota data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [token]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Quota Monitoring</h1>
        <Button variant="outline" onClick={load}>Refresh</Button>
      </div>

      {error && (
        <Card className="border-destructive/30">
          <CardContent className="pt-6 text-destructive">{error}</CardContent>
        </Card>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2"><ShieldAlert className="h-4 w-4" /> Limits</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <p><strong>User:</strong> {data?.limits.user_requests_per_minute ?? 0} requests/min</p>
            <p><strong>Guild:</strong> {data?.limits.guild_requests_per_minute ?? 0} requests/min</p>
            <p className="text-muted-foreground">Window: {data?.usage.window_seconds ?? 60}s</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Currently Tracked</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <p><strong>Users:</strong> {data?.usage.tracked_users ?? 0}</p>
            <p><strong>Guilds:</strong> {data?.usage.tracked_guilds ?? 0}</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2"><User className="h-4 w-4" /> Top Users (Last Minute)</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {(data?.usage.top_users ?? []).length === 0 ? (
              <p className="text-sm text-muted-foreground">No user activity in current window.</p>
            ) : (
              data?.usage.top_users.map((item, idx) => (
                <div key={`${item.user_id}-${idx}`} className="flex items-center justify-between rounded-md border p-2 text-sm">
                  <span className="font-mono">{item.user_id}</span>
                  <span>{item.requests_last_minute} req</span>
                </div>
              ))
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2"><Building2 className="h-4 w-4" /> Top Guilds (Last Minute)</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {(data?.usage.top_guilds ?? []).length === 0 ? (
              <p className="text-sm text-muted-foreground">No guild activity in current window.</p>
            ) : (
              data?.usage.top_guilds.map((item, idx) => (
                <div key={`${item.guild_id}-${idx}`} className="flex items-center justify-between rounded-md border p-2 text-sm">
                  <span className="font-mono">{item.guild_id}</span>
                  <span>{item.requests_last_minute} req</span>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
