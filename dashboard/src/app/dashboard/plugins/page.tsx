"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { useSession } from "next-auth/react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { api, PluginInfo, CatalogPlugin } from "@/lib/api";
import { toast } from "sonner";
import { PlusCircle, Download, Zap, BookOpen, Upload } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export default function PluginsPage() {
  const router = useRouter();
  const { data: session } = useSession();
  const [installedPlugins, setInstalledPlugins] = useState<PluginInfo[]>([]);
  const [catalogPlugins, setCatalogPlugins] = useState<CatalogPlugin[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState("installed");
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const token = (session as { accessToken?: string })?.accessToken;

  const refreshPlugins = async (authToken: string) => {
    try {
      const overview = await api.getPluginsOverview(authToken);
      setInstalledPlugins(overview.plugins);
      setCatalogPlugins(overview.catalog);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to load plugins");
    }
  };

  useEffect(() => {
    if (!token) {
      router.push("/login");
      return;
    }

    const loadPlugins = async () => {
      try {
        setLoading(true);
        await refreshPlugins(token);
      } catch (error) {
        toast.error(error instanceof Error ? error.message : "Failed to load plugins");
      } finally {
        setLoading(false);
      }
    };

    loadPlugins();
  }, [token, router]);

  const handleEnable = async (pluginName: string) => {
    try {
      setActionLoading(pluginName);
      const result = await api.enablePlugin(token || "", pluginName);
      toast.success(result.message);
      await refreshPlugins(token || "");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : `Failed to enable plugin "${pluginName}"`);
    } finally {
      setActionLoading(null);
    }
  };

  const handleDisable = async (pluginName: string) => {
    try {
      setActionLoading(pluginName);
      const result = await api.disablePlugin(token || "", pluginName);
      toast.success(result.message);
      await refreshPlugins(token || "");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : `Failed to disable plugin "${pluginName}"`);
    } finally {
      setActionLoading(null);
    }
  };

  const handleInstall = async (pluginName: string) => {
    try {
      setActionLoading(pluginName);
      const result = await api.installPlugin(token || "", pluginName);
      toast.success(result.message);
      setActiveTab("installed");
      await refreshPlugins(token || "");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : `Failed to install plugin "${pluginName}"`);
    } finally {
      setActionLoading(null);
    }
  };

  const handleUninstall = async (pluginName: string) => {
    if (!confirm(`Are you sure you want to uninstall "${pluginName}"? This will remove all plugin files.`)) {
      return;
    }
    
    try {
      setActionLoading(pluginName);
      const result = await api.uninstallPlugin(token || "", pluginName);
      toast.success(result.message);
      await refreshPlugins(token || "");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : `Failed to uninstall plugin "${pluginName}"`);
    } finally {
      setActionLoading(null);
    }
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.name.endsWith('.zip')) {
      toast.error("Please upload a .zip file");
      return;
    }

    try {
      setUploading(true);
      const result = await api.uploadPlugin(token || "", file);
      toast.success(result.message);
      setActiveTab("installed");
      await refreshPlugins(token || "");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to upload plugin");
    } finally {
      setUploading(false);
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  // Poll plugin state periodically while this tab is visible
  useEffect(() => {
    if (!token) return;

    const interval = setInterval(() => {
      if (document.visibilityState !== "visible") {
        return;
      }
      refreshPlugins(token).catch(() => {
        // Silently fail on background refresh
      });
    }, 15000);

    return () => clearInterval(interval);
  }, [token]);

  const availableToInstall = catalogPlugins.filter(p => !p.installed);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Plugins</h1>
        <p className="text-gray-600 mt-2">Install and manage plugins to extend SparkSage functionality</p>
      </div>

      {/* Upload Plugin Card */}
      <Card className="bg-gradient-to-r from-purple-50 to-blue-50 border-purple-200">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-purple-900">
            <Upload className="h-5 w-5" />
            Upload Custom Plugin
          </CardTitle>
          <CardDescription>
            Install a plugin from a local ZIP file
          </CardDescription>
        </CardHeader>
        <CardContent>
          <input
            ref={fileInputRef}
            type="file"
            accept=".zip"
            onChange={handleFileChange}
            className="hidden"
          />
          <Button
            onClick={handleUploadClick}
            disabled={uploading}
            variant="outline"
            className="border-purple-300 text-purple-700 hover:bg-purple-100"
          >
            {uploading ? (
              <>
                <PlusCircle className="h-4 w-4 mr-2 animate-spin" />
                Uploading...
              </>
            ) : (
              <>
                <Upload className="h-4 w-4 mr-2" />
                Choose ZIP File
              </>
            )}
          </Button>
          <p className="text-xs text-gray-500 mt-2">
            Upload a plugin ZIP file containing manifest.json and cog files
          </p>
        </CardContent>
      </Card>

      {/* Instant Command Updates Info */}
      <Card className="bg-gradient-to-r from-green-50 to-teal-50 border-green-200">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-green-900 text-lg">
            <Zap className="h-5 w-5" />
            ⚡ Instant Plugin Commands
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <p className="text-green-800">
            <strong>✅ Commands update dynamically!</strong> When you enable/disable plugins, their commands are automatically loaded/unloaded without restarting the bot.
          </p>
          <div className="bg-white/50 rounded-lg p-3 space-y-2">
            <p className="font-medium text-green-900">For INSTANT command updates in Discord:</p>
            <ol className="list-decimal list-inside space-y-1 text-green-800 ml-2">
              <li>Set <code className="bg-green-100 px-1.5 py-0.5 rounded text-xs font-mono">DISCORD_GUILD_ID</code> in your <code className="bg-green-100 px-1.5 py-0.5 rounded text-xs font-mono">.env</code> file</li>
              <li>Get your server ID by right-clicking your Discord server → Copy Server ID</li>
              <li>Enable/disable plugins - commands appear instantly! ⚡</li>
            </ol>
            <p className="text-xs text-green-700 mt-2">
              💡 <strong>Without DISCORD_GUILD_ID:</strong> Global sync takes up to 1 hour for commands to appear.
            </p>
          </div>
        </CardContent>
      </Card>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="installed">
            Installed ({installedPlugins.length})
          </TabsTrigger>
          <TabsTrigger value="catalog">
            Available ({availableToInstall.length})
          </TabsTrigger>
        </TabsList>

        {/* Installed Plugins Tab */}
        <TabsContent value="installed" className="space-y-6 mt-6">
          {loading ? (
            <Card>
              <CardContent className="pt-6 text-center">
                <PlusCircle className="h-12 w-12 text-gray-300 mx-auto mb-4 animate-spin" />
                <p className="text-gray-600">Loading installed plugins...</p>
              </CardContent>
            </Card>
          ) : installedPlugins.length === 0 ? (
            <Card>
              <CardContent className="pt-6 text-center">
                <PlusCircle className="h-12 w-12 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-600">No plugins installed yet</p>
                <p className="text-sm text-gray-400 mt-2">Browse the catalog to install your first plugin</p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4 grid-cols-1 lg:grid-cols-2">
              {installedPlugins.map((plugin) => (
                <Card 
                  key={plugin.name} 
                  className={plugin.loaded ? "border-green-200 bg-green-50" : "border-gray-200"}
                >
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <CardTitle className="flex items-center gap-2">
                          {plugin.name}
                          {plugin.loaded && (
                            <Badge variant="default" className="bg-green-600">
                              ✅ Loaded
                            </Badge>
                          )}
                          {!plugin.loaded && plugin.enabled && (
                            <Badge variant="secondary">
                              ⏳ Enabled
                            </Badge>
                          )}
                          {!plugin.loaded && !plugin.enabled && (
                            <Badge variant="outline">
                              ❌ Disabled
                            </Badge>
                          )}
                        </CardTitle>
                        <CardDescription className="text-sm">v{plugin.version}</CardDescription>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <p className="text-sm text-gray-700">{plugin.description}</p>

                    <div className="space-y-2 text-sm">
                      <div className="flex items-center gap-2 text-gray-600">
                        <BookOpen className="h-4 w-4" />
                        <span>{plugin.author}</span>
                      </div>
                      {plugin.cog_name && (
                        <div className="flex items-center gap-2 text-gray-600">
                          <Zap className="h-4 w-4" />
                          <span>Cog: {plugin.cog_name}</span>
                        </div>
                      )}
                    </div>

                    <div className="flex gap-2 pt-2 flex-wrap">
                      {plugin.enabled ? (
                        <Button
                          variant="destructive"
                          size="sm"
                          onClick={() => handleDisable(plugin.name)}
                          disabled={actionLoading === plugin.name}
                        >
                          {actionLoading === plugin.name ? "Disabling..." : "Disable"}
                        </Button>
                      ) : (
                        <Button
                          variant="default"
                          size="sm"
                          onClick={() => handleEnable(plugin.name)}
                          disabled={actionLoading === plugin.name}
                        >
                          {actionLoading === plugin.name ? "Enabling..." : "Enable"}
                        </Button>
                      )}
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleUninstall(plugin.name)}
                        disabled={actionLoading === plugin.name}
                        className="border-red-300 text-red-600 hover:bg-red-50 hover:text-red-700"
                      >
                        {actionLoading === plugin.name ? "Removing..." : "Uninstall"}
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* Catalog Tab */}
        <TabsContent value="catalog" className="space-y-6 mt-6">
          {loading ? (
            <Card>
              <CardContent className="pt-6 text-center">
                <Download className="h-12 w-12 text-gray-300 mx-auto mb-4 animate-spin" />
                <p className="text-gray-600">Loading plugin catalog...</p>
              </CardContent>
            </Card>
          ) : availableToInstall.length === 0 ? (
            <Card>
              <CardContent className="pt-6 text-center">
                <Download className="h-12 w-12 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-600">All catalog plugins are installed!</p>
                <p className="text-sm text-gray-400 mt-2">Check back later for new plugins</p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4 grid-cols-1 lg:grid-cols-2">
              {availableToInstall.map((plugin) => (
                <Card key={plugin.name} className="border-blue-200 bg-blue-50">
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <CardTitle className="flex items-center gap-2">
                          {plugin.name}
                          <Badge variant="outline" className="bg-blue-100 text-blue-900">
                            ⭐ New
                          </Badge>
                        </CardTitle>
                        <CardDescription className="text-sm">v{plugin.version}</CardDescription>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <p className="text-sm text-gray-700">{plugin.description}</p>

                    <div className="space-y-2 text-sm">
                      <div className="flex items-center gap-2 text-gray-600">
                        <BookOpen className="h-4 w-4" />
                        <span>{plugin.author}</span>
                      </div>
                      {plugin.tags && (
                        <div className="flex flex-wrap gap-1">
                          {plugin.tags.map((tag) => (
                            <Badge key={tag} variant="secondary" className="text-xs">
                              {tag}
                            </Badge>
                          ))}
                        </div>
                      )}
                      {plugin.requires_config && (
                        <div className="bg-yellow-100 text-yellow-800 text-xs p-2 rounded">
                          ⚠️ Requires configuration
                        </div>
                      )}
                    </div>

                    <div className="flex gap-2 pt-2 flex-wrap">
                      <Button
                        variant="default"
                        size="sm"
                        onClick={() => handleInstall(plugin.name)}
                        disabled={actionLoading === plugin.name}
                        className="bg-blue-600 hover:bg-blue-700"
                      >
                        {actionLoading === plugin.name ? (
                          <>
                            <PlusCircle className="h-4 w-4 mr-2 animate-spin" />
                            Installing...
                          </>
                        ) : (
                          <>
                            <Download className="h-4 w-4 mr-2" />
                            Install
                          </>
                        )}
                      </Button>
                      <a href={plugin.repo} target="_blank" rel="noopener noreferrer">
                        <Button variant="outline" size="sm">
                          <BookOpen className="h-4 w-4 mr-2" />
                          Docs
                        </Button>
                      </a>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {/* Catalog Info */}
          <Card className="bg-blue-50 border-blue-200">
            <CardHeader>
              <CardTitle className="text-blue-900">🎉 SparkSage Plugin Catalog</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm text-blue-800">
              <p>
                Browse and install plugins from the official SparkSage catalog. These community-created plugins 
                extend bot functionality with games, moderation tools, statistics, and more.
              </p>
              <ul className="list-disc list-inside space-y-1">
                <li>Click "Install" to add a plugin to your server</li>
                <li>Switch to "Installed" tab to enable/disable plugins</li>
                <li>Each plugin comes with documentation</li>
                <li>Some plugins may require configuration after installation</li>
              </ul>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* How to Create Section */}
      <Card className="bg-purple-50 border-purple-200">
        <CardHeader>
          <CardTitle className="text-purple-900">🚀 Create Your Own Plugin</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm text-purple-800">
          <p>
            Want to extend SparkSage? Creating a plugin is easy! Check out the plugin documentation 
            to learn how to build and distribute your own plugins.
          </p>
          <ol className="list-decimal list-inside space-y-2 ml-2">
            <li>Create a directory in <code className="bg-white px-2 py-1 rounded text-purple-900">plugins/your_plugin_name/</code></li>
            <li>Add a <code className="bg-white px-2 py-1 rounded text-purple-900">manifest.json</code> with plugin metadata</li>
            <li>Create a Python file with a Discord Cog class</li>
            <li>Test your plugin using Discord commands</li>
            <li>Share with the community!</li>
          </ol>
          <p className="pt-2">
            Read the <a href="#" className="underline font-semibold">plugin developer guide</a> for detailed instructions.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
