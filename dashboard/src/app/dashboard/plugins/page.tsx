"use client";

import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import {
  AlertCircle,
  Download,
  Trash2,
  Power,
  PowerOff,
  RefreshCw,
  Info,
} from "lucide-react";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";

interface PluginItem {
  name: string;
  version: string;
  author: string;
  description: string;
  installed: boolean;
  enabled: boolean;
}

export default function PluginsPage() {
  const { data: session } = useSession();
  const [plugins, setPlugins] = useState<PluginItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionInProgress, setActionInProgress] = useState<string | null>(null);

  const token = (session as { accessToken?: string })?.accessToken;

  const loadPlugins = async () => {
    if (!token) return;
    try {
      setLoading(true);
      const response = await api.getPlugins?.(token);
      if (response && "plugins" in response) {
        setPlugins(response.plugins);
      }
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Failed to load plugins"
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPlugins();
  }, [token]);

  const handleInstall = async (pluginName: string) => {
    if (!token) return;
    try {
      setActionInProgress(pluginName);
      await api.installPlugin?.(token, pluginName);
      toast.success(`Installed ${pluginName}`);
      await loadPlugins();
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Failed to install plugin"
      );
    } finally {
      setActionInProgress(null);
    }
  };

  const handleEnable = async (pluginName: string) => {
    if (!token) return;
    try {
      setActionInProgress(pluginName);
      await api.enablePlugin?.(token, pluginName);
      toast.success(`Enabled ${pluginName}. Restart bot to load.`);
      await loadPlugins();
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Failed to enable plugin"
      );
    } finally {
      setActionInProgress(null);
    }
  };

  const handleDisable = async (pluginName: string) => {
    if (!token) return;
    try {
      setActionInProgress(pluginName);
      await api.disablePlugin?.(token, pluginName);
      toast.success(`Disabled ${pluginName}. Restart bot to unload.`);
      await loadPlugins();
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Failed to disable plugin"
      );
    } finally {
      setActionInProgress(null);
    }
  };

  const handleUninstall = async (pluginName: string) => {
    if (!token) return;
    if (!confirm(`Uninstall ${pluginName}? This cannot be undone.`)) return;

    try {
      setActionInProgress(pluginName);
      await api.uninstallPlugin?.(token, pluginName);
      toast.success(`Uninstalled ${pluginName}`);
      await loadPlugins();
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Failed to uninstall plugin"
      );
    } finally {
      setActionInProgress(null);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Community Plugins</h1>
        <Button
          onClick={loadPlugins}
          disabled={loading}
          variant="outline"
          size="sm"
        >
          <RefreshCw className="mr-2 h-4 w-4" />
          Refresh
        </Button>
      </div>

      {/* Information Card */}
      <Card className="border-blue-200 bg-blue-50">
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <Info className="h-4 w-4" />
            About Plugins
          </CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-blue-800 space-y-2">
          <p>
            SparkSage plugins are community-contributed cogs that extend bot functionality.
          </p>
          <ul className="list-disc list-inside space-y-1">
            <li>
              <strong>Available:</strong> Plugin exists in {`plugins/`} directory but not installed
            </li>
            <li>
              <strong>Installed:</strong> Plugin metadata saved but not enabled
            </li>
            <li>
              <strong>Enabled:</strong> Plugin will load when bot starts
            </li>
            <li>
              <strong>Note:</strong> Restart bot after enabling/disabling plugins
            </li>
          </ul>
        </CardContent>
      </Card>

      {/* Plugins Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {loading ? (
          <div className="col-span-full text-center py-8 text-muted-foreground">
            Loading plugins...
          </div>
        ) : plugins.length === 0 ? (
          <div className="col-span-full text-center py-8 text-muted-foreground">
            No plugins found
          </div>
        ) : (
          plugins.map((plugin) => (
            <Card key={plugin.name} className="flex flex-col">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1">
                    <CardTitle className="text-base font-semibold">
                      {plugin.name}
                    </CardTitle>
                    <p className="text-xs text-muted-foreground mt-1">
                      v{plugin.version} by {plugin.author}
                    </p>
                  </div>
                  {plugin.enabled && (
                    <Badge className="bg-green-100 text-green-800">
                      Enabled
                    </Badge>
                  )}
                  {plugin.installed && !plugin.enabled && (
                    <Badge variant="outline">Installed</Badge>
                  )}
                  {!plugin.installed && (
                    <Badge variant="secondary">Available</Badge>
                  )}
                </div>
              </CardHeader>
              <CardContent className="flex-1 flex flex-col justify-between gap-4">
                <p className="text-sm text-muted-foreground">
                  {plugin.description || "No description provided"}
                </p>

                <div className="flex gap-2">
                  {!plugin.installed ? (
                    <Button
                      className="flex-1"
                      size="sm"
                      onClick={() => handleInstall(plugin.name)}
                      disabled={actionInProgress === plugin.name}
                    >
                      <Download className="mr-2 h-4 w-4" />
                      Install
                    </Button>
                  ) : (
                    <>
                      {!plugin.enabled ? (
                        <Button
                          className="flex-1"
                          size="sm"
                          variant="outline"
                          onClick={() => handleEnable(plugin.name)}
                          disabled={actionInProgress === plugin.name}
                        >
                          <Power className="mr-2 h-4 w-4" />
                          Enable
                        </Button>
                      ) : (
                        <Button
                          className="flex-1"
                          size="sm"
                          variant="outline"
                          onClick={() => handleDisable(plugin.name)}
                          disabled={actionInProgress === plugin.name}
                        >
                          <PowerOff className="mr-2 h-4 w-4" />
                          Disable
                        </Button>
                      )}
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => handleUninstall(plugin.name)}
                        disabled={actionInProgress === plugin.name}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </>
                  )}
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
