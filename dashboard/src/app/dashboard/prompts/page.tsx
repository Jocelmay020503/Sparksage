"use client";

import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import { api, ChannelPromptItem } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Loader2, Trash2 } from "lucide-react";
import { toast } from "sonner";

export default function PromptsPage() {
  const { data: session } = useSession();
  const token = (session as { accessToken?: string })?.accessToken;

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [items, setItems] = useState<ChannelPromptItem[]>([]);

  const [guildId, setGuildId] = useState("");
  const [channelId, setChannelId] = useState("");
  const [systemPrompt, setSystemPrompt] = useState("");

  async function load() {
    if (!token) return;
    try {
      const res = await api.getChannelPrompts(token, guildId || undefined);
      setItems(res.channel_prompts);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to load channel prompts");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [token]);

  async function onSave() {
    if (!token) return;
    if (!guildId || !channelId || !systemPrompt.trim()) {
      toast.error("Guild ID, Channel ID, and Prompt are required");
      return;
    }

    setSaving(true);
    try {
      await api.createChannelPrompt(token, {
        guild_id: guildId,
        channel_id: channelId,
        system_prompt: systemPrompt.trim(),
      });
      toast.success("Channel prompt saved");
      setSystemPrompt("");
      await load();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to save prompt");
    } finally {
      setSaving(false);
    }
  }

  async function onDelete(id: string) {
    if (!token) return;
    try {
      await api.deleteChannelPrompt(token, id);
      toast.success("Channel prompt removed");
      await load();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to remove prompt");
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
        <h1 className="text-2xl font-bold">Channel Prompts</h1>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Set Channel Prompt</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="guild-id">Guild ID</Label>
              <Input id="guild-id" value={guildId} onChange={(e) => setGuildId(e.target.value)} placeholder="123456789012345678" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="channel-id">Channel ID</Label>
              <Input id="channel-id" value={channelId} onChange={(e) => setChannelId(e.target.value)} placeholder="123456789012345678" />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="prompt">System Prompt</Label>
            <Textarea
              id="prompt"
              value={systemPrompt}
              onChange={(e) => setSystemPrompt(e.target.value)}
              placeholder="You are a strict technical assistant..."
              className="min-h-32"
            />
          </div>

          <div className="flex justify-end">
            <Button onClick={onSave} disabled={saving}>
              {saving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Save Prompt
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Configured Channels</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {items.length === 0 ? (
              <p className="text-sm text-muted-foreground">No channel prompts configured yet.</p>
            ) : (
              items.map((item) => (
                <div key={item.channel_id} className="rounded-md border p-3 space-y-2">
                  <div className="flex items-center justify-between gap-3">
                    <div className="text-sm">
                      <p><span className="font-medium">Guild:</span> {item.guild_id}</p>
                      <p><span className="font-medium">Channel:</span> {item.channel_id}</p>
                    </div>
                    <Button variant="destructive" size="sm" onClick={() => onDelete(item.channel_id)}>
                      <Trash2 className="mr-1 h-3 w-3" /> Remove
                    </Button>
                  </div>
                  <p className="text-xs text-muted-foreground whitespace-pre-wrap">
                    {item.system_prompt.length > 300
                      ? `${item.system_prompt.slice(0, 300)}...`
                      : item.system_prompt}
                  </p>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
