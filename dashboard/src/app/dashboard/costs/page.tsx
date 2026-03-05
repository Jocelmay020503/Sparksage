"use client";

import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import {
  TrendingDown,
  Users,
  Building,
  Clock,
  DollarSign,
  AlertCircle,
} from "lucide-react";
import { api } from "@/lib/api";
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

interface CostSummary {
  total_cost: number;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  query_count: number;
  costs_by_provider: Record<string, number>;
}

interface CostByProvider {
  provider: string;
  total_cost: number;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  query_count: number;
}

interface CostHistoryItem {
  date: string;
  cost: number;
  provider_count: number;
}

interface TopItem {
  user_id?: string;
  guild_id?: string;
  total_cost: number;
  total_tokens: number;
  query_count: number;
}

const COLORS = ["#3b82f6", "#ef4444", "#10b981", "#f59e0b", "#8b5cf6"];

function formatCost(cost: number): string {
  if (cost >= 1) {
    return `$${cost.toFixed(2)}`;
  } else if (cost >= 0.001) {
    return `$${(cost * 1000).toFixed(2)}m`;
  } else {
    return `$${(cost * 1000000).toFixed(2)}µ`;
  }
}

export default function CostsDashboard() {
  const { data: session } = useSession();
  const [timeRange, setTimeRange] = useState<TimeRange>(30);
  const [summary, setSummary] = useState<CostSummary | null>(null);
  const [providers, setProviders] = useState<CostByProvider[]>([]);
  const [history, setHistory] = useState<CostHistoryItem[]>([]);
  const [topUsers, setTopUsers] = useState<TopItem[]>([]);
  const [topGuilds, setTopGuilds] = useState<TopItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const token = (session as { accessToken?: string })?.accessToken;

  useEffect(() => {
    if (!token) return;

    const loadCosts = async () => {
      try {
        setLoading(true);
        setError(null);

        const [summaryResult, providersResult, historyResult, usersResult, guildsResult] =
          await Promise.allSettled([
            api.getCostSummary?.(token, timeRange),
            api.getCostByProvider?.(token, timeRange),
            api.getCostHistory?.(token, timeRange),
            api.getTopExpensiveUsers?.(token, timeRange, 5),
            api.getTopExpensiveGuilds?.(token, timeRange, 5),
          ]);

        if (summaryResult.status === "fulfilled" && summaryResult.value) {
          setSummary(summaryResult.value);
        }
        if (providersResult.status === "fulfilled" && providersResult.value) {
          setProviders(providersResult.value.costs_by_provider || []);
        }
        if (historyResult.status === "fulfilled" && historyResult.value) {
          setHistory(historyResult.value.history || []);
        }
        if (usersResult.status === "fulfilled" && usersResult.value) {
          const normalizedTopUsers: TopItem[] = (usersResult.value.top_users || []).map((item) => ({
            user_id: item.user_id,
            guild_id: item.guild_id,
            total_cost: Number(item.total_cost ?? 0),
            total_tokens: Number(item.total_tokens ?? 0),
            query_count: Number(item.query_count ?? 0),
          }));
          setTopUsers(normalizedTopUsers);
        }
        if (guildsResult.status === "fulfilled" && guildsResult.value) {
          const normalizedTopGuilds: TopItem[] = (guildsResult.value.top_guilds || []).map((item) => ({
            user_id: item.user_id,
            guild_id: item.guild_id,
            total_cost: Number(item.total_cost ?? 0),
            total_tokens: Number(item.total_tokens ?? 0),
            query_count: Number(item.query_count ?? 0),
          }));
          setTopGuilds(normalizedTopGuilds);
        }
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to load costs"
        );
      } finally {
        setLoading(false);
      }
    };

    loadCosts();
  }, [token, timeRange]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <h1 className="text-2xl font-bold">Cost Tracking</h1>
        <div className="flex flex-wrap gap-2">
          {([7, 14, 30, 60, 90] as TimeRange[]).map((range) => (
            <Button
              key={range}
              variant={timeRange === range ? "default" : "outline"}
              onClick={() => setTimeRange(range)}
              size="sm"
              className="text-xs sm:text-sm"
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
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Total Cost</CardTitle>
            <DollarSign className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {loading ? "-" : formatCost(summary?.total_cost ?? 0)}
            </div>
            <p className="text-xs text-muted-foreground">
              Last {timeRange} days
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Input Tokens</CardTitle>
            <TrendingDown className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {loading ? "-" : (summary?.input_tokens ?? 0).toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground">
              User messages
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Output Tokens</CardTitle>
            <TrendingDown className="h-4 w-4 text-purple-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {loading ? "-" : (summary?.output_tokens ?? 0).toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground">
              Bot responses
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Queries</CardTitle>
            <Clock className="h-4 w-4 text-amber-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {loading ? "-" : (summary?.query_count ?? 0).toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground">
              AI interactions
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Avg Cost</CardTitle>
            <DollarSign className="h-4 w-4 text-indigo-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {loading || !summary || summary.query_count === 0
                ? "-"
                : formatCost(summary.total_cost / summary.query_count)}
            </div>
            <p className="text-xs text-muted-foreground">
              Per query
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid gap-6 sm:grid-cols-1 lg:grid-cols-2">
        {/* Daily Costs */}
        <Card>
          <CardHeader>
            <CardTitle>Daily Costs</CardTitle>
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
                  <Tooltip
                    formatter={(value) =>
                      typeof value === "number" ? formatCost(value) : value
                    }
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="cost"
                    stroke="#3b82f6"
                    name="Cost (USD)"
                    dot={{ r: 4 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        {/* Provider Costs */}
        <Card>
          <CardHeader>
            <CardTitle>Costs by Provider</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="h-64 flex items-center justify-center text-muted-foreground">
                Loading...
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={providers}
                    dataKey="total_cost"
                    nameKey="provider"
                    cx="50%"
                    cy="50%"
                    outerRadius={100}
                    label={(entry) => {
                      const data = entry as unknown as CostByProvider;
                      return `${data.provider}: ${formatCost(data.total_cost)}`;
                    }}
                  >
                    {providers.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value) => formatCost(value as number)} />
                </PieChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Provider Breakdown Table */}
      <Card className="overflow-x-auto">
        <CardHeader>
          <CardTitle>Provider Cost Breakdown</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm min-w-[500px]">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2 px-2">Provider</th>
                  <th className="text-right py-2 px-2">Cost</th>
                  <th className="text-right py-2 px-2">Queries</th>
                  <th className="text-right py-2 px-2 hidden sm:table-cell">Input Tokens</th>
                  <th className="text-right py-2 px-2 hidden sm:table-cell">Output Tokens</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={5} className="text-center py-4 text-muted-foreground">
                      Loading...
                    </td>
                  </tr>
                ) : providers.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="text-center py-4 text-muted-foreground">
                      No data available
                    </td>
                  </tr>
                ) : (
                  providers.map((provider) => (
                    <tr key={provider.provider} className="border-b hover:bg-muted/50">
                      <td className="py-2 px-2 font-medium">
                        {provider.provider}
                      </td>
                      <td className="text-right py-2 px-2 font-mono">
                        {formatCost(provider.total_cost)}
                      </td>
                      <td className="text-right py-2 px-2 text-muted-foreground">
                        {provider.query_count}
                      </td>
                      <td className="text-right py-2 px-2 text-muted-foreground hidden sm:table-cell">
                        {provider.input_tokens.toLocaleString()}
                      </td>
                      <td className="text-right py-2 px-2 text-muted-foreground hidden sm:table-cell">
                        {provider.output_tokens.toLocaleString()}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Top Users and Guilds */}
      <div className="grid gap-6 sm:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-4 w-4" />
              Top Users (Last {timeRange}d)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {loading ? (
                <div className="text-center py-4 text-muted-foreground">
                  Loading...
                </div>
              ) : topUsers.length === 0 ? (
                <div className="text-center py-4 text-muted-foreground">
                  No data available
                </div>
              ) : (
                topUsers.map((user, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between p-2 rounded hover:bg-muted"
                  >
                    <span className="font-mono text-sm">@{user.user_id}</span>
                    <div className="text-right">
                      <div className="font-semibold">
                        {formatCost(user.total_cost)}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {user.total_tokens.toLocaleString()} tokens
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Building className="h-4 w-4" />
              Top Guilds (Last {timeRange}d)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {loading ? (
                <div className="text-center py-4 text-muted-foreground">
                  Loading...
                </div>
              ) : topGuilds.length === 0 ? (
                <div className="text-center py-4 text-muted-foreground">
                  No data available
                </div>
              ) : (
                topGuilds.map((guild, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between p-2 rounded hover:bg-muted"
                  >
                    <span className="font-mono text-sm">{guild.guild_id}</span>
                    <div className="text-right">
                      <div className="font-semibold">
                        {formatCost(guild.total_cost)}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {guild.total_tokens.toLocaleString()} tokens
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Pricing Info */}
      <Card className="border-blue-200 bg-blue-50">
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <DollarSign className="h-4 w-4" />
            About Cost Tracking
          </CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-blue-800 space-y-2">
          <p>
            SparkSage tracks API costs based on token usage from each provider.
          </p>
          <ul className="list-disc list-inside space-y-1">
            <li>
              <strong>Input Tokens:</strong> Tokens in user messages and conversation history
            </li>
            <li>
              <strong>Output Tokens:</strong> Tokens in bot responses
            </li>
            <li>
              <strong>Provider Cost:</strong> Varies by provider and model
            </li>
            <li>
              <strong>Free Providers:</strong> Groq provides free API access during beta
            </li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}
