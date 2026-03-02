"use client";

import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import { Loader2, Trash2, Shield } from "lucide-react";

import { api } from "@/lib/api";
import type { PermissionItem } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";

export default function PermissionsPage() {
  const { data: session } = useSession();
  const token = (session as { accessToken?: string })?.accessToken;

  const [permissions, setPermissions] = useState<PermissionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  const [guildId, setGuildId] = useState("");
  const [commandName, setCommandName] = useState("");
  const [roleId, setRoleId] = useState("");

  async function load() {
    if (!token) return;
    try {
      const result = await api.getPermissions(token, guildId || undefined);
      setPermissions(result.permissions);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to load permissions");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [token]);

  async function handleCreate() {
    if (!token) return;
    if (!guildId.trim() || !commandName.trim() || !roleId.trim()) {
      toast.error("Guild ID, command name, and role ID are required");
      return;
    }

    setSubmitting(true);
    try {
      await api.createPermission(token, {
        guild_id: guildId.trim(),
        command_name: commandName.trim(),
        role_id: roleId.trim(),
      });
      toast.success(`Permission added for /${commandName}`);
      setCommandName("");
      setRoleId("");
      await load();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to create permission");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(perm: PermissionItem) {
    if (!token) return;
    try {
      await api.deletePermission(token, perm.command_name, perm.guild_id, perm.role_id);
      toast.success(`Removed permission for /${perm.command_name}`);
      await load();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to delete permission");
    }
  }

  // Group permissions by command
  const byCommand: Record<string, PermissionItem[]> = {};
  for (const perm of permissions) {
    if (!byCommand[perm.command_name]) {
      byCommand[perm.command_name] = [];
    }
    byCommand[perm.command_name].push(perm);
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Shield className="h-6 w-6" />
          Command Permissions
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          Restrict commands to specific roles. Unrestricted commands are available to everyone.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Add Permission</CardTitle>
          <CardDescription>
            Require a Discord role to use a specific command
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <Input
            placeholder="Guild ID (Discord Server ID)"
            value={guildId}
            onChange={(e) => setGuildId(e.target.value)}
          />
          <Input
            placeholder="Command name (e.g., ask, review, summarize)"
            value={commandName}
            onChange={(e) => setCommandName(e.target.value)}
          />
          <Input
            placeholder="Role ID (Discord Role ID)"
            value={roleId}
            onChange={(e) => setRoleId(e.target.value)}
          />
          <div className="flex gap-2">
            <Button onClick={handleCreate} disabled={submitting}>
              {submitting ? "Adding..." : "Add Permission"}
            </Button>
            <Button variant="outline" onClick={load}>
              Refresh
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Active Permissions ({permissions.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : permissions.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No command restrictions set. All commands are available to everyone.
            </p>
          ) : (
            <div className="space-y-4">
              {Object.entries(byCommand)
                .sort(([a], [b]) => a.localeCompare(b))
                .map(([cmd, perms]) => (
                  <div key={cmd} className="rounded-md border p-3">
                    <div className="mb-2 flex items-center gap-2">
                      <Badge variant="default" className="font-mono">
                        /{cmd}
                      </Badge>
                      <span className="text-sm text-muted-foreground">
                        {perms.length} role{perms.length !== 1 ? "s" : ""} required
                      </span>
                    </div>
                    <div className="space-y-2">
                      {perms.map((perm, idx) => (
                        <div
                          key={idx}
                          className="flex items-center justify-between rounded-sm bg-muted/50 p-2 text-sm"
                        >
                          <div className="space-y-0.5">
                            <div className="font-mono text-xs">Role: {perm.role_id}</div>
                            <div className="font-mono text-xs text-muted-foreground">
                              Guild: {perm.guild_id}
                            </div>
                          </div>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => handleDelete(perm)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
