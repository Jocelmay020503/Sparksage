"use client";

import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import { api, ChannelProviderItem, ProviderItem } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Loader2, Trash2 } from "lucide-react";
import { toast } from "sonner";

export default function ChannelProvidersPage() {
  const { data: session } = useSession();
  const token = (session as { accessToken?: string })?.accessToken;

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [items, setItems] = useState<ChannelProviderItem[]>([]);
  const [providers, setProviders] = useState<ProviderItem[]>([]);

  const [guildId, setGuildId] = useState("");
  const [channelId, setChannelId] = useState("");
  const [provider, setProvider] = useState("gemini");

  async function load() {
    if (!token) return;
    try {
      const [mappingRes, providerRes] = await Promise.all([
        api.getChannelProviders(token, guildId || undefined),
        api.getProviders(token),
      ]);
      setItems(mappingRes.channel_providers);
      setProviders(providerRes.providers);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to load channel provider mappings");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [token]);

  async function onSave() {
    if (!token) return;
    if (!guildId || !channelId || !provider) {
      toast.error("Guild ID, Channel ID, and Provider are required");
      return;
    }

    setSaving(true);
    try {
      await api.createChannelProvider(token, {
        guild_id: guildId,
        channel_id: channelId,
        provider,
      });
      toast.success("Channel provider override saved");
      await load();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to save channel provider override");
    } finally {
      setSaving(false);
    }
  }

  async function onDelete(id: string) {
    if (!token) return;
    try {
      await api.deleteChannelProvider(token, id);
      toast.success("Channel provider override removed");
      await load();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to remove channel provider override");
    }
  }

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
        <h1 className="text-2xl font-bold">Channel Provider Overrides</h1>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Set Channel Provider</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="guild-id">Guild ID</Label>
              <Input
                id="guild-id"
                value={guildId}
                onChange={(e) => setGuildId(e.target.value)}
                placeholder="123456789012345678"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="channel-id">Channel ID</Label>
              <Input
                id="channel-id"
                value={channelId}
                onChange={(e) => setChannelId(e.target.value)}
                placeholder="123456789012345678"
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="provider">Provider</Label>
            <select
              id="provider"
              className="h-9 w-full rounded-md border bg-background px-3 text-sm"
              value={provider}
              onChange={(e) => setProvider(e.target.value)}
            >
              {providers.map((p) => (
                <option key={p.name} value={p.name}>
                  {p.display_name} ({p.name})
                </option>
              ))}
            </select>
          </div>

          <div className="flex justify-end">
            <Button onClick={onSave} disabled={saving}>
              {saving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Save Override
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Configured Channel Overrides</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {items.length === 0 ? (
              <p className="text-sm text-muted-foreground">No channel provider overrides configured yet.</p>
            ) : (
              items.map((item) => (
                <div key={item.channel_id} className="rounded-md border p-3">
                  <div className="flex items-center justify-between gap-3">
                    <div className="text-sm">
                      <p><span className="font-medium">Guild:</span> {item.guild_id}</p>
                      <p><span className="font-medium">Channel:</span> {item.channel_id}</p>
                      <p><span className="font-medium">Provider:</span> {item.provider}</p>
                    </div>
                    <Button variant="destructive" size="sm" onClick={() => onDelete(item.channel_id)}>
                      <Trash2 className="mr-1 h-3 w-3" /> Remove
                    </Button>
                  </div>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
