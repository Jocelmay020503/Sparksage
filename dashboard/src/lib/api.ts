const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface FetchOptions extends RequestInit {
  token?: string;
}

async function apiFetch<T>(path: string, options: FetchOptions = {}): Promise<T> {
  const { token, headers: customHeaders, ...rest } = options;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((customHeaders as Record<string, string>) || {}),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_URL}${path}`, {
    headers,
    ...rest,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail || `API error: ${res.status}`);
  }

  return res.json();
}

// Response types matching backend
export interface ProviderItem {
  name: string;
  display_name: string;
  model: string;
  free: boolean;
  configured: boolean;
  is_primary: boolean;
}

export interface ProvidersResponse {
  providers: ProviderItem[];
  fallback_order: string[];
}

export interface ChannelItem {
  channel_id: string;
  message_count: number;
  last_active: string;
}

export interface MessageItem {
  role: string;
  content: string;
  provider: string | null;
  created_at: string;
}

export interface FAQItem {
  id: number;
  guild_id: string;
  question: string;
  answer: string;
  match_keywords: string;
  times_used: number;
  created_by: string | null;
  created_at: string;
}

export interface PermissionItem {
  command_name: string;
  guild_id: string;
  role_id: string;
}

export interface ChannelPromptItem {
  channel_id: string;
  guild_id: string;
  system_prompt: string;
  created_at: string;
  updated_at: string;
}

export interface ChannelProviderItem {
  channel_id: string;
  guild_id: string;
  provider: string;
  created_at: string;
  updated_at: string;
}

export interface AnalyticsSummary {
  total_events: number;
  events_by_type: Record<string, number>;
  events_by_provider: Record<string, number>;
  total_tokens: number;
  avg_latency_ms: number;
}

export interface AnalyticsHistoryItem {
  date: string;
  event_type: string;
  count: number;
  total_tokens: number;
  avg_latency_ms: number;
  provider: string | null;
}

export interface TopChannelItem {
  channel_id: string;
  count: number;
  total_tokens: number;
}

export interface TopUserItem {
  user_id: string;
  count: number;
  total_tokens: number;
}

export interface BotStatus {
  online: boolean;
  latency: number | null;
  guilds: number;
  uptime: number | null;
}

export interface TestProviderResult {
  success: boolean;
  message: string;
  latency_ms?: number;
}

export const api = {
  // Auth
  login: (password: string) =>
    apiFetch<{ access_token: string; token_type: string }>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ password }),
    }),

  me: (token: string) =>
    apiFetch<{ username: string; role: string }>("/api/auth/me", { token }),

  // Config
  getConfig: (token: string) =>
    apiFetch<{ config: Record<string, string> }>("/api/config", { token }),

  updateConfig: (token: string, values: Record<string, string>) =>
    apiFetch<{ status: string }>("/api/config", {
      method: "PUT",
      body: JSON.stringify({ values }),
      token,
    }),

  // Providers
  getProviders: (token: string) =>
    apiFetch<ProvidersResponse>("/api/providers", { token }),

  testProvider: (token: string, provider: string) =>
    apiFetch<TestProviderResult>("/api/providers/test", {
      method: "POST",
      body: JSON.stringify({ provider }),
      token,
    }),

  setPrimaryProvider: (token: string, provider: string) =>
    apiFetch<{ status: string; primary: string }>("/api/providers/primary", {
      method: "PUT",
      body: JSON.stringify({ provider }),
      token,
    }),

  // Bot
  getBotStatus: (token: string) =>
    apiFetch<BotStatus>("/api/bot/status", { token }),

  // Conversations
  getConversations: (token: string) =>
    apiFetch<{ channels: ChannelItem[] }>("/api/conversations", { token }),

  getConversation: (token: string, channelId: string) =>
    apiFetch<{ channel_id: string; messages: MessageItem[] }>(
      `/api/conversations/${channelId}`,
      { token }
    ),
  deleteConversation: (token: string, channelId: string) =>
    apiFetch<{ status: string }>(`/api/conversations/${channelId}`, {
      method: "DELETE",
      token,
    }),

  // FAQs
  getFaqs: (token: string, guildId?: string) => {
    const suffix = guildId
      ? `?guild_id=${encodeURIComponent(guildId)}`
      : "";
    return apiFetch<{ faqs: FAQItem[] }>(`/api/faqs${suffix}`, { token });
  },

  createFaq: (
    token: string,
    payload: {
      guild_id: string;
      question: string;
      answer: string;
      match_keywords: string;
      created_by?: string;
    }
  ) =>
    apiFetch<{ id: number; status: string }>("/api/faqs", {
      method: "POST",
      body: JSON.stringify(payload),
      token,
    }),

  deleteFaq: (token: string, faqId: number, guildId?: string) => {
    const suffix = guildId
      ? `?guild_id=${encodeURIComponent(guildId)}`
      : "";
    return apiFetch<{ status: string }>(`/api/faqs/${faqId}${suffix}`, {
      method: "DELETE",
      token,
    });
  },

  // Permissions
  getPermissions: (token: string, guildId?: string, commandName?: string) => {
    const params = new URLSearchParams();
    if (guildId) params.set("guild_id", guildId);
    if (commandName) params.set("command_name", commandName);
    const suffix = params.toString() ? `?${params.toString()}` : "";
    return apiFetch<{ permissions: PermissionItem[] }>(`/api/permissions${suffix}`, { token });
  },

  createPermission: (
    token: string,
    payload: {
      command_name: string;
      guild_id: string;
      role_id: string;
    }
  ) =>
    apiFetch<{ status: string }>("/api/permissions", {
      method: "POST",
      body: JSON.stringify(payload),
      token,
    }),

  deletePermission: (token: string, commandName: string, guildId: string, roleId: string) =>
    apiFetch<{ status: string }>(
      `/api/permissions?command_name=${encodeURIComponent(commandName)}&guild_id=${encodeURIComponent(guildId)}&role_id=${encodeURIComponent(roleId)}`,
      {
        method: "DELETE",
        token,
      }
    ),

  // Channel Prompts
  getChannelPrompts: (token: string, guildId?: string) => {
    const suffix = guildId
      ? `?guild_id=${encodeURIComponent(guildId)}`
      : "";
    return apiFetch<{ channel_prompts: ChannelPromptItem[] }>(`/api/channel-prompts${suffix}`, { token });
  },

  getChannelPrompt: (token: string, channelId: string) =>
    apiFetch<{ channel_id: string; system_prompt: string }>(
      `/api/channel-prompts/${encodeURIComponent(channelId)}`,
      { token }
    ),

  createChannelPrompt: (
    token: string,
    payload: {
      channel_id: string;
      guild_id: string;
      system_prompt: string;
    }
  ) =>
    apiFetch<{ status: string; channel_id: string }>("/api/channel-prompts", {
      method: "POST",
      body: JSON.stringify(payload),
      token,
    }),

  updateChannelPrompt: (
    token: string,
    channelId: string,
    guildId: string,
    systemPrompt: string
  ) =>
    apiFetch<{ status: string; channel_id: string }>(
      `/api/channel-prompts/${encodeURIComponent(channelId)}?guild_id=${encodeURIComponent(guildId)}`,
      {
        method: "PUT",
        body: JSON.stringify({ system_prompt: systemPrompt }),
        token,
      }
    ),

  deleteChannelPrompt: (token: string, channelId: string) =>
    apiFetch<{ status: string; channel_id: string }>(
      `/api/channel-prompts/${encodeURIComponent(channelId)}`,
      {
        method: "DELETE",
        token,
      }
    ),

  // Channel Providers
  getChannelProviders: (token: string, guildId?: string) => {
    const suffix = guildId
      ? `?guild_id=${encodeURIComponent(guildId)}`
      : "";
    return apiFetch<{ channel_providers: ChannelProviderItem[] }>(`/api/channel-providers${suffix}`, { token });
  },

  getChannelProvider: (token: string, channelId: string) =>
    apiFetch<{ channel_id: string; provider: string }>(
      `/api/channel-providers/${encodeURIComponent(channelId)}`,
      { token }
    ),

  createChannelProvider: (
    token: string,
    payload: {
      channel_id: string;
      guild_id: string;
      provider: string;
    }
  ) =>
    apiFetch<{ status: string; channel_id: string; provider: string }>("/api/channel-providers", {
      method: "POST",
      body: JSON.stringify(payload),
      token,
    }),

  deleteChannelProvider: (token: string, channelId: string) =>
    apiFetch<{ status: string; channel_id: string }>(
      `/api/channel-providers/${encodeURIComponent(channelId)}`,
      {
        method: "DELETE",
        token,
      }
    ),

  // Wizard
  getWizardStatus: (token: string) =>
    apiFetch<{ completed: boolean; current_step: number }>("/api/wizard/status", { token }),

  completeWizard: (token: string, data: Record<string, string>) =>
    apiFetch<{ status: string }>("/api/wizard/complete", {
      method: "POST",
      body: JSON.stringify({ config: data }),
      token,
    }),

  // Analytics
  getAnalyticsSummary: (token: string, days: number = 7) =>
    apiFetch<AnalyticsSummary>(`/api/analytics/summary?days=${days}`, { token }),

  getAnalyticsHistory: (token: string, days: number = 7, eventType?: string) => {
    const params = new URLSearchParams();
    params.set("days", days.toString());
    if (eventType) params.set("event_type", eventType);
    const suffix = params.toString() ? `?${params.toString()}` : "";
    return apiFetch<AnalyticsHistoryItem[]>(`/api/analytics/history${suffix}`, { token });
  },

  getTopChannels: (token: string, limit: number = 10) =>
    apiFetch<TopChannelItem[]>(`/api/analytics/top-channels?limit=${limit}`, { token }),

  getTopUsers: (token: string, limit: number = 10) =>
    apiFetch<TopUserItem[]>(`/api/analytics/top-users?limit=${limit}`, { token }),
};
