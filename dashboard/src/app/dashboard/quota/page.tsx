"use client";

import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import { AlertCircle, Users, Building, Clock, TrendingDown } from "lucide-react";
import { api } from "@/lib/api";
import type {
  QuotaStatsResponse,
  QuotaViolationItem,
} from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

type TimeRange = 1 | 6 | 24 | 72;

const violationTypeColors: Record<string, string> = {
  user_limit: "bg-red-100 text-red-800",
  guild_limit: "bg-orange-100 text-orange-800",
};

const violationTypeLabels: Record<string, string> = {
  user_limit: "User Rate Limit",
  guild_limit: "Guild Rate Limit",
};

export default function QuotaDashboard() {
  const { data: session } = useSession();
  const [timeRange, setTimeRange] = useState<TimeRange>(24);
  const [stats, setStats] = useState<QuotaStatsResponse | null>(null);
  const [violations, setViolations] = useState<QuotaViolationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const token = (session as { accessToken?: string })?.accessToken;

  useEffect(() => {
    if (!token) return;

    const loadQuotaData = async () => {
      try {
        setLoading(true);
        setError(null);

        const [statsResult, violationsResult] = await Promise.allSettled([
          api.getQuotaStatus(token, timeRange),
          api.getQuotaViolations(token, timeRange),
        ]);

        if (statsResult.status === "fulfilled") {
          setStats(statsResult.value);
        }
        if (violationsResult.status === "fulfilled") {
          setViolations(violationsResult.value);
        }
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to load quota data"
        );
      } finally {
        setLoading(false);
      }
    };

    loadQuotaData();
  }, [token, timeRange]);

  const getTimeRangeLabel = (hours: TimeRange) => {
    const labels: Record<TimeRange, string> = {
      1: "1h",
      6: "6h",
      24: "24h",
      72: "72h",
    };
    return labels[hours];
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Rate Limiting & Quotas</h1>
        <div className="flex gap-2">
          {([1, 6, 24, 72] as TimeRange[]).map((range) => (
            <Button
              key={range}
              variant={timeRange === range ? "default" : "outline"}
              onClick={() => setTimeRange(range)}
              size="sm"
            >
              {getTimeRangeLabel(range)}
            </Button>
          ))}
        </div>
      </div>

      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="flex items-center gap-2 pt-6">
            <AlertCircle className="h-5 w-5 text-red-600" />
            <span className="text-sm text-red-800">{error}</span>
          </CardContent>
        </Card>
      )}

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">
              Total Violations
            </CardTitle>
            <AlertCircle className="h-4 w-4 text-red-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {loading ? "-" : stats?.total_violations ?? 0}
            </div>
            <p className="text-xs text-muted-foreground">
              Last {getTimeRangeLabel(timeRange)}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">User Limits</CardTitle>
            <Users className="h-4 w-4 text-orange-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {loading ? "-" : stats?.user_limit_violations ?? 0}
            </div>
            <p className="text-xs text-muted-foreground">
              Per-user rate limits
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Guild Limits</CardTitle>
            <Building className="h-4 w-4 text-amber-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {loading ? "-" : stats?.guild_limit_violations ?? 0}
            </div>
            <p className="text-xs text-muted-foreground">
              Per-guild rate limits
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">
              Users Affected
            </CardTitle>
            <Users className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {loading ? "-" : stats?.unique_users_affected ?? 0}
            </div>
            <p className="text-xs text-muted-foreground">
              Unique users
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">
              Guilds Affected
            </CardTitle>
            <Building className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {loading ? "-" : stats?.unique_guilds_affected ?? 0}
            </div>
            <p className="text-xs text-muted-foreground">
              Unique guilds
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Rate Limiting Configuration */}
      <Card>
        <CardHeader>
          <CardTitle>Rate Limiting Configuration</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <p className="text-sm font-medium">Per-User Limit</p>
              <p className="text-2xl font-bold">30 requests</p>
              <p className="text-xs text-muted-foreground">
                Per 60-second window
              </p>
            </div>
            <div className="space-y-2">
              <p className="text-sm font-medium">Per-Guild Limit</p>
              <p className="text-2xl font-bold">300 requests</p>
              <p className="text-xs text-muted-foreground">
                Per 60-second window
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Violations Table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingDown className="h-4 w-4" />
            Recent Violations (Last {getTimeRangeLabel(timeRange)})
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2 px-2">Type</th>
                  <th className="text-left py-2 px-2">User ID</th>
                  <th className="text-left py-2 px-2">Guild ID</th>
                  <th className="text-left py-2 px-2">Reset At</th>
                  <th className="text-left py-2 px-2">Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={5} className="text-center py-4 text-muted-foreground">
                      Loading...
                    </td>
                  </tr>
                ) : violations.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="text-center py-4 text-muted-foreground">
                      No violations in this time period
                    </td>
                  </tr>
                ) : (
                  violations.map((violation) => (
                    <tr
                      key={violation.id}
                      className="border-b hover:bg-muted/50"
                    >
                      <td className="py-2 px-2">
                        <Badge
                          className={
                            violationTypeColors[violation.violation_type] ||
                            "bg-gray-100 text-gray-800"
                          }
                        >
                          {violationTypeLabels[violation.violation_type] ||
                            violation.violation_type}
                        </Badge>
                      </td>
                      <td className="py-2 px-2 font-mono text-xs">
                        {violation.user_id}
                      </td>
                      <td className="py-2 px-2 font-mono text-xs">
                        {violation.guild_id}
                      </td>
                      <td className="py-2 px-2 text-xs text-muted-foreground">
                        {new Date(violation.limit_reset_at).toLocaleTimeString()}
                      </td>
                      <td className="py-2 px-2 text-xs text-muted-foreground">
                        {new Date(violation.created_at).toLocaleString()}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Information Card */}
      <Card className="border-blue-200 bg-blue-50">
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <Clock className="h-4 w-4" />
            About Rate Limiting
          </CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-blue-800 space-y-2">
          <p>
            SparkSage implements sliding window rate limiting to prevent abuse
            and manage resource usage.
          </p>
          <ul className="list-disc list-inside space-y-1">
            <li>
              <strong>User Limit:</strong> Each user can make 30 requests per 60
              seconds
            </li>
            <li>
              <strong>Guild Limit:</strong> Each guild can make 300 requests per
              60 seconds
            </li>
            <li>
              <strong>Overlapping:</strong> Both limits are enforced
              independently
            </li>
            <li>
              <strong>Violations:</strong> Tracked and logged for monitoring and
              debugging
            </li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}
