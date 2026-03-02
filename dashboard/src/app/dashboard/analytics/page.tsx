"use client";

import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import {
  Activity,
  BarChart3,
  TrendingUp,
  Users,
  Clock,
  AlertCircle,
} from "lucide-react";
import { api } from "@/lib/api";
import type {
  AnalyticsSummary,
  AnalyticsHistoryItem,
  TopChannelItem,
  TopUserItem,
} from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

type TimeRange = 7 | 14 | 30 | 60 | 90;

export default function AnalyticsDashboard() {
  const { data: session } = useSession();
  const [timeRange, setTimeRange] = useState<TimeRange>(7);
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [history, setHistory] = useState<AnalyticsHistoryItem[]>([]);
  const [topChannels, setTopChannels] = useState<TopChannelItem[]>([]);
  const [topUsers, setTopUsers] = useState<TopUserItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const token = (session as { accessToken?: string })?.accessToken;

  useEffect(() => {
    if (!token) return;

    const loadAnalytics = async () => {
      try {
        setLoading(true);
        setError(null);

        const [summaryResult, historyResult, channelsResult, usersResult] =
          await Promise.allSettled([
            api.getAnalyticsSummary(token, timeRange),
            api.getAnalyticsHistory(token, timeRange),
            api.getTopChannels(token, 5),
            api.getTopUsers(token, 5),
          ]);

        if (summaryResult.status === "fulfilled") {
          setSummary(summaryResult.value);
        }
        if (historyResult.status === "fulfilled") {
          setHistory(historyResult.value);
        }
        if (channelsResult.status === "fulfilled") {
          setTopChannels(channelsResult.value);
        }
        if (usersResult.status === "fulfilled") {
          setTopUsers(usersResult.value);
        }
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to load analytics"
        );
      } finally {
        setLoading(false);
      }
    };

    loadAnalytics();
  }, [token, timeRange]);

  const COLORS = [
    "#3b82f6",
    "#ef4444",
    "#10b981",
    "#f59e0b",
    "#8b5cf6",
    "#ec4899",
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Analytics</h1>
        <div className="flex gap-2">
          {([7, 14, 30, 60, 90] as TimeRange[]).map((range) => (
            <Button
              key={range}
              variant={timeRange === range ? "default" : "outline"}
              onClick={() => setTimeRange(range)}
              size="sm"
            >
              {range}d
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
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Total Events</CardTitle>
            <Activity className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {loading ? "-" : summary?.total_events ?? 0}
            </div>
            <p className="text-xs text-muted-foreground">
              Last {timeRange} days
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Total Tokens</CardTitle>
            <TrendingUp className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {loading ? "-" : (summary?.total_tokens ?? 0).toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground">
              Used across providers
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Avg Latency</CardTitle>
            <Clock className="h-4 w-4 text-amber-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {loading ? "-" : `${(summary?.avg_latency_ms ?? 0).toFixed(0)}ms`}
            </div>
            <p className="text-xs text-muted-foreground">
              Response time
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Providers</CardTitle>
            <BarChart3 className="h-4 w-4 text-purple-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {loading ? "-" : summary?.unique_providers ?? 0}
            </div>
            <p className="text-xs text-muted-foreground">
              Active providers
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Daily Activity */}
        <Card>
          <CardHeader>
            <CardTitle>Daily Activity</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="h-64 flex items-center justify-center text-muted-foreground">
                Loading...
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={history}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="date"
                    tick={{ fontSize: 12 }}
                    angle={-45}
                    textAnchor="end"
                    height={80}
                  />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="count"
                    stroke="#3b82f6"
                    name="Events"
                    dot={{ r: 4 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="avg_latency"
                    stroke="#f59e0b"
                    name="Avg Latency (ms)"
                    yAxisId="right"
                    dot={{ r: 4 }}
                  />
                  <YAxis yAxisId="right" orientation="right" />
                </LineChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        {/* Top Channels */}
        <Card>
          <CardHeader>
            <CardTitle>Top Channels</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="h-64 flex items-center justify-center text-muted-foreground">
                Loading...
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={topChannels}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="channel_id"
                    tick={{ fontSize: 12 }}
                    angle={-45}
                    textAnchor="end"
                    height={80}
                  />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="count" fill="#3b82f6" name="Events" />
                  <Bar dataKey="tokens" fill="#10b981" name="Tokens" />
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Summary Tables */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Top Channels Table */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-4 w-4" />
              Top Channels (Last {timeRange}d)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-2 px-2">Channel ID</th>
                    <th className="text-right py-2 px-2">Events</th>
                    <th className="text-right py-2 px-2">Tokens</th>
                  </tr>
                </thead>
                <tbody>
                  {loading ? (
                    <tr>
                      <td colSpan={3} className="text-center py-4 text-muted-foreground">
                        Loading...
                      </td>
                    </tr>
                  ) : topChannels.length === 0 ? (
                    <tr>
                      <td colSpan={3} className="text-center py-4 text-muted-foreground">
                        No data available
                      </td>
                    </tr>
                  ) : (
                    topChannels.map((channel, i) => (
                      <tr key={i} className="border-b hover:bg-muted/50">
                        <td className="py-2 px-2 font-mono text-xs">
                          #{channel.channel_id}
                        </td>
                        <td className="text-right py-2 px-2">
                          {channel.count}
                        </td>
                        <td className="text-right py-2 px-2 text-muted-foreground">
                          {channel.tokens.toLocaleString()}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

        {/* Top Users Table */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-4 w-4" />
              Top Users (Last {timeRange}d)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-2 px-2">User ID</th>
                    <th className="text-right py-2 px-2">Events</th>
                    <th className="text-right py-2 px-2">Tokens</th>
                  </tr>
                </thead>
                <tbody>
                  {loading ? (
                    <tr>
                      <td colSpan={3} className="text-center py-4 text-muted-foreground">
                        Loading...
                      </td>
                    </tr>
                  ) : topUsers.length === 0 ? (
                    <tr>
                      <td colSpan={3} className="text-center py-4 text-muted-foreground">
                        No data available
                      </td>
                    </tr>
                  ) : (
                    topUsers.map((user, i) => (
                      <tr key={i} className="border-b hover:bg-muted/50">
                        <td className="py-2 px-2 font-mono text-xs">
                          @{user.user_id}
                        </td>
                        <td className="text-right py-2 px-2">
                          {user.count}
                        </td>
                        <td className="text-right py-2 px-2 text-muted-foreground">
                          {user.tokens.toLocaleString()}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
