"use client";

import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { MessageSquare, TrendingUp, Zap, Activity } from "lucide-react";
import { api } from "@/lib/api";
import type { AnalyticsSummary, AnalyticsHistoryItem, TopChannelItem, TopUserItem } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

const COLORS = ["#3b82f6", "#ef4444", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899"];

export default function AnalyticsDashboard() {
  const { data: session } = useSession();
  const [days, setDays] = useState("7");
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [history, setHistory] = useState<AnalyticsHistoryItem[]>([]);
  const [topChannels, setTopChannels] = useState<TopChannelItem[]>([]);
  const [topUsers, setTopUsers] = useState<TopUserItem[]>([]);
  const [loading, setLoading] = useState(true);

  const token = (session as { accessToken?: string })?.accessToken;

  useEffect(() => {
    if (!token) return;
    setLoading(true);
    Promise.allSettled([
      api.getAnalyticsSummary(token, parseInt(days)),
      api.getAnalyticsHistory(token, parseInt(days)),
      api.getTopChannels(token, 10),
      api.getTopUsers(token, 10),
    ]).then(([summaryResult, historyResult, channelsResult, usersResult]) => {
      if (summaryResult.status === "fulfilled") setSummary(summaryResult.value);
      if (historyResult.status === "fulfilled") setHistory(historyResult.value);
      if (channelsResult.status === "fulfilled") setTopChannels(channelsResult.value);
      if (usersResult.status === "fulfilled") setTopUsers(usersResult.value);
      setLoading(false);
    });
  }, [token, days]);

  if (loading) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold">Analytics</h1>
        <p className="text-muted-foreground">Loading analytics data...</p>
      </div>
    );
  }

  // Prepare data for daily activity chart
  const dailyData = history.reduce((acc, item) => {
    const existing = acc.find((d) => d.date === item.date);
    if (existing) {
      existing.count += item.count;
      existing.latency = (existing.latency + item.avg_latency_ms) / 2;
    } else {
      acc.push({
        date: item.date,
        count: item.count,
        latency: item.avg_latency_ms,
      });
    }
    return acc;
  }, [] as Array<{ date: string; count: number; latency: number }>);

  // Prepare provider distribution data
  const providerData = summary
    ? Object.entries(summary.events_by_provider).map(([name, count]) => ({
        name: name || "Unknown",
        value: count,
      }))
    : [];

  // Prepare event type data
  const eventTypeData = summary
    ? Object.entries(summary.events_by_type).map(([type, count]) => ({
        name: type.replace("_", " ").toUpperCase(),
        value: count,
      }))
    : [];

  const dayOptions = [
    { value: "7", label: "Last 7 days" },
    { value: "14", label: "Last 14 days" },
    { value: "30", label: "Last 30 days" },
    { value: "60", label: "Last 60 days" },
    { value: "90", label: "Last 90 days" },
  ];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Analytics</h1>
        <div className="flex gap-2">
          {dayOptions.map((option) => (
            <Button
              key={option.value}
              variant={days === option.value ? "default" : "outline"}
              size="sm"
              onClick={() => setDays(option.value)}
            >
              {option.label}
            </Button>
          ))}
        </div>
      </div>

      {/* Summary cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Total Events</CardTitle>
            <Activity className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{summary?.total_events || 0}</p>
            <p className="text-xs text-muted-foreground">AI interactions tracked</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Total Tokens</CardTitle>
            <Zap className="h-4 w-4 text-amber-600" />
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{summary?.total_tokens?.toLocaleString() || 0}</p>
            <p className="text-xs text-muted-foreground">Tokens consumed</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Avg Latency</CardTitle>
            <TrendingUp className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{summary?.avg_latency_ms?.toFixed(0) || 0}ms</p>
            <p className="text-xs text-muted-foreground">Average response time</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Providers Used</CardTitle>
            <MessageSquare className="h-4 w-4 text-purple-600" />
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">
              {summary?.events_by_provider ? Object.keys(summary.events_by_provider).length : 0}
            </p>
            <p className="text-xs text-muted-foreground">Active AI providers</p>
          </CardContent>
        </Card>
      </div>

      {/* Charts section */}
      <div className="grid gap-4 lg:grid-cols-2">
        {/* Daily Activity Chart */}
        {dailyData.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Daily Activity</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={dailyData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="count"
                    stroke="#3b82f6"
                    name="Events"
                    strokeWidth={2}
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        )}

        {/* Provider Distribution Chart */}
        {providerData.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Provider Usage</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={providerData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, value, percent }) => `${name}: ${percent ? (percent * 100).toFixed(0) : 0}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {providerData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        )}

        {/* Event Type Distribution */}
        {eventTypeData.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Event Types</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={eventTypeData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="value" fill="#3b82f6" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        )}

        {/* Latency Trend */}
        {dailyData.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Response Latency Trend</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={dailyData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip formatter={(value: unknown) => {
                    if (typeof value === "number") {
                      return `${value.toFixed(0)}ms`;
                    }
                    return value as string;
                  }} />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="latency"
                    stroke="#ef4444"
                    name="Latency (ms)"
                    strokeWidth={2}
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Top Channels and Users */}
      <div className="grid gap-4 lg:grid-cols-2">
        {/* Top Channels */}
        {topChannels.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Top Channels</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {topChannels.slice(0, 5).map((channel, idx) => (
                  <div key={channel.channel_id} className="flex items-center justify-between pb-2 border-b last:border-b-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-muted-foreground">#{idx + 1}</span>
                      <span className="text-sm font-medium truncate">Channel {channel.channel_id}</span>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-semibold">{channel.count}</p>
                      <p className="text-xs text-muted-foreground">{(channel.total_tokens || 0).toLocaleString()} tokens</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Top Users */}
        {topUsers.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Top Users</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {topUsers.slice(0, 5).map((user, idx) => (
                  <div key={user.user_id} className="flex items-center justify-between pb-2 border-b last:border-b-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-muted-foreground">#{idx + 1}</span>
                      <span className="text-sm font-medium truncate">User {user.user_id}</span>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-semibold">{user.count}</p>
                      <p className="text-xs text-muted-foreground">{(user.total_tokens || 0).toLocaleString()} tokens</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
