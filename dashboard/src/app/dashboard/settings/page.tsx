"use client";

import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Loader2, Save, RotateCcw } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Slider } from "@/components/ui/slider";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { toast } from "sonner";

const settingsSchema = z.object({
  DISCORD_TOKEN: z.string().min(1, "Discord token is required"),
  BOT_PREFIX: z.string().min(1).max(5),
  MAX_TOKENS: z.number().min(128).max(4096),
  SYSTEM_PROMPT: z.string().min(1),
  WELCOME_ENABLED: z.enum(["true", "false"]),
  WELCOME_CHANNEL_ID: z.string(),
  WELCOME_MESSAGE: z.string().min(1),
  DIGEST_ENABLED: z.enum(["true", "false"]),
  DIGEST_CHANNEL_ID: z.string(),
  DIGEST_TIME: z.string(),
  GEMINI_API_KEY: z.string(),
  GROQ_API_KEY: z.string(),
  OPENROUTER_API_KEY: z.string(),
  ANTHROPIC_API_KEY: z.string(),
  OPENAI_API_KEY: z.string(),
});

type SettingsForm = z.infer<typeof settingsSchema>;

const DEFAULTS: SettingsForm = {
  DISCORD_TOKEN: "",
  BOT_PREFIX: "!",
  MAX_TOKENS: 1024,
  SYSTEM_PROMPT:
    "You are SparkSage, a helpful and friendly AI assistant in a Discord server. Be concise, helpful, and engaging.",
  WELCOME_ENABLED: "false",
  WELCOME_CHANNEL_ID: "",
  WELCOME_MESSAGE: "Welcome {user} to **{server}**! 👋",
  DIGEST_ENABLED: "false",
  DIGEST_CHANNEL_ID: "",
  DIGEST_TIME: "09:00",
  GEMINI_API_KEY: "",
  GROQ_API_KEY: "",
  OPENROUTER_API_KEY: "",
  ANTHROPIC_API_KEY: "",
  OPENAI_API_KEY: "",
};

export default function SettingsPage() {
  const { data: session } = useSession();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const token = (session as { accessToken?: string })?.accessToken;

  const form = useForm<SettingsForm>({
    resolver: zodResolver(settingsSchema),
    defaultValues: DEFAULTS,
  });

  useEffect(() => {
    if (!token) return;
    api
      .getConfig(token)
      .then(({ config }) => {
        const mapped: Partial<SettingsForm> = {};
        for (const key of Object.keys(DEFAULTS) as (keyof SettingsForm)[]) {
          if (config[key] !== undefined) {
            if (key === "MAX_TOKENS") {
              mapped[key] = Number(config[key]);
            } else {
              (mapped as Record<string, string>)[key] = config[key];
            }
          }
        }
        form.reset({ ...DEFAULTS, ...mapped });
      })
      .catch(() => toast.error("Failed to load settings"))
      .finally(() => setLoading(false));
  }, [token]);

  async function onSubmit(values: SettingsForm) {
    if (!token) return;
    setSaving(true);
    try {
      // Convert to string values for the API, skip masked values (***...)
      const payload: Record<string, string> = {};
      for (const [key, val] of Object.entries(values)) {
        const strVal = String(val);
        if (!strVal.startsWith("***")) {
          payload[key] = strVal;
        }
      }
      await api.updateConfig(token, payload);
      toast.success("Settings saved successfully");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to save settings");
    } finally {
      setSaving(false);
    }
  }

  function handleReset() {
    form.reset(DEFAULTS);
  }

  const maxTokens = form.watch("MAX_TOKENS");
  const systemPrompt = form.watch("SYSTEM_PROMPT");
  const welcomeEnabled = form.watch("WELCOME_ENABLED");
  const digestEnabled = form.watch("DIGEST_ENABLED");

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
        <h1 className="text-2xl font-bold">Settings</h1>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={handleReset}>
            <RotateCcw className="mr-1 h-3 w-3" /> Reset to Defaults
          </Button>
        </div>
      </div>

      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        {/* Discord */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Discord</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="discord-token">Bot Token</Label>
              <Input
                id="discord-token"
                type="password"
                {...form.register("DISCORD_TOKEN")}
              />
              {form.formState.errors.DISCORD_TOKEN && (
                <p className="text-xs text-destructive">
                  {form.formState.errors.DISCORD_TOKEN.message}
                </p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Bot Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Bot Behavior</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="prefix">Command Prefix</Label>
              <Input
                id="prefix"
                {...form.register("BOT_PREFIX")}
                className="w-24"
              />
              {form.formState.errors.BOT_PREFIX && (
                <p className="text-xs text-destructive">
                  {form.formState.errors.BOT_PREFIX.message}
                </p>
              )}
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label>Max Tokens</Label>
                <span className="text-sm font-mono tabular-nums text-muted-foreground">
                  {maxTokens}
                </span>
              </div>
              <Slider
                value={[maxTokens]}
                onValueChange={([val]) => form.setValue("MAX_TOKENS", val)}
                min={128}
                max={4096}
                step={64}
              />
            </div>

            <Separator />

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="system-prompt">System Prompt</Label>
                <span className="text-xs text-muted-foreground">
                  {systemPrompt?.length || 0} characters
                </span>
              </div>
              <Textarea
                id="system-prompt"
                {...form.register("SYSTEM_PROMPT")}
                rows={4}
              />
            </div>

            <Separator />

            <div className="space-y-3">
              <Label>Onboarding Enabled</Label>
              <RadioGroup
                value={welcomeEnabled}
                onValueChange={(value) =>
                  form.setValue("WELCOME_ENABLED", value as "true" | "false")
                }
                className="grid grid-cols-2 gap-3"
              >
                <div className="flex items-center gap-2 rounded-md border p-2">
                  <RadioGroupItem value="true" id="welcome-enabled-true" />
                  <Label htmlFor="welcome-enabled-true" className="cursor-pointer">
                    Enabled
                  </Label>
                </div>
                <div className="flex items-center gap-2 rounded-md border p-2">
                  <RadioGroupItem value="false" id="welcome-enabled-false" />
                  <Label htmlFor="welcome-enabled-false" className="cursor-pointer">
                    Disabled
                  </Label>
                </div>
              </RadioGroup>
            </div>

            <div className="space-y-2">
              <Label htmlFor="welcome-channel">Welcome Channel ID (optional)</Label>
              <Input
                id="welcome-channel"
                placeholder="123456789012345678"
                {...form.register("WELCOME_CHANNEL_ID")}
              />
              <p className="text-xs text-muted-foreground">
                If empty, welcome is sent via DM. If set, message posts in this channel.
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="welcome-message">Welcome Message Template</Label>
              <Textarea
                id="welcome-message"
                rows={3}
                {...form.register("WELCOME_MESSAGE")}
              />
              <p className="text-xs text-muted-foreground">
                Supports placeholders: {"{user}"}, {"{server}"}
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Daily Digest */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Daily Digest</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-3">
              <Label>Daily Digest Enabled</Label>
              <RadioGroup
                value={digestEnabled}
                onValueChange={(value) =>
                  form.setValue("DIGEST_ENABLED", value as "true" | "false")
                }
                className="grid grid-cols-2 gap-3"
              >
                <div className="flex items-center gap-2 rounded-md border p-2">
                  <RadioGroupItem value="true" id="digest-enabled-true" />
                  <Label htmlFor="digest-enabled-true" className="cursor-pointer">
                    Enabled
                  </Label>
                </div>
                <div className="flex items-center gap-2 rounded-md border p-2">
                  <RadioGroupItem value="false" id="digest-enabled-false" />
                  <Label htmlFor="digest-enabled-false" className="cursor-pointer">
                    Disabled
                  </Label>
                </div>
              </RadioGroup>
              <p className="text-xs text-muted-foreground">
                Automatically summarize daily server activity and post to a designated channel
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="digest-channel">Digest Channel ID</Label>
              <Input
                id="digest-channel"
                placeholder="123456789012345678"
                {...form.register("DIGEST_CHANNEL_ID")}
              />
              <p className="text-xs text-muted-foreground">
                Channel where the daily digest will be posted
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="digest-time">Digest Time (UTC)</Label>
              <Input
                id="digest-time"
                type="time"
                placeholder="09:00"
                {...form.register("DIGEST_TIME")}
                className="w-40"
              />
              <p className="text-xs text-muted-foreground">
                Time of day to post the digest (format: HH:MM in UTC timezone)
              </p>
            </div>
          </CardContent>
        </Card>

        {/* API Keys */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">API Keys</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-xs text-muted-foreground">
              Masked values (***...) are not overwritten on save. Enter a new value to update.
            </p>
            {(
              [
                ["GEMINI_API_KEY", "Gemini"],
                ["GROQ_API_KEY", "Groq"],
                ["OPENROUTER_API_KEY", "OpenRouter"],
                ["ANTHROPIC_API_KEY", "Anthropic"],
                ["OPENAI_API_KEY", "OpenAI"],
              ] as const
            ).map(([key, label]) => (
              <div key={key} className="space-y-1">
                <Label htmlFor={key}>{label}</Label>
                <Input
                  id={key}
                  type="password"
                  {...form.register(key)}
                  className="font-mono text-sm"
                />
              </div>
            ))}
          </CardContent>
        </Card>

        <Button type="submit" disabled={saving} className="w-full">
          {saving ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <Save className="mr-2 h-4 w-4" />
          )}
          Save Settings
        </Button>
      </form>
    </div>
  );
}
