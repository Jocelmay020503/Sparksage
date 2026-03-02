"use client";

import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import { Loader2, Trash2 } from "lucide-react";

import { api } from "@/lib/api";
import type { FAQItem } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";

export default function FaqsPage() {
  const { data: session } = useSession();
  const token = (session as { accessToken?: string })?.accessToken;

  const [faqs, setFaqs] = useState<FAQItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  const [guildId, setGuildId] = useState("");
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [keywords, setKeywords] = useState("");

  async function load() {
    if (!token) return;
    try {
      const result = await api.getFaqs(token, guildId || undefined);
      setFaqs(result.faqs);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to load FAQs");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [token]);

  async function handleCreate() {
    if (!token) return;
    if (!guildId.trim() || !question.trim() || !answer.trim() || !keywords.trim()) {
      toast.error("Guild ID, question, answer, and keywords are required");
      return;
    }

    setSubmitting(true);
    try {
      await api.createFaq(token, {
        guild_id: guildId.trim(),
        question: question.trim(),
        answer: answer.trim(),
        match_keywords: keywords.trim(),
      });
      toast.success("FAQ created");
      setQuestion("");
      setAnswer("");
      setKeywords("");
      await load();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to create FAQ");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(id: number) {
    if (!token) return;
    try {
      await api.deleteFaq(token, id, guildId || undefined);
      toast.success(`Deleted FAQ #${id}`);
      await load();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to delete FAQ");
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">FAQs</h1>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Create FAQ</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <Input
            placeholder="Guild ID (required)"
            value={guildId}
            onChange={(e) => setGuildId(e.target.value)}
          />
          <Input
            placeholder="Question"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
          />
          <Textarea
            placeholder="Answer"
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
          />
          <Input
            placeholder="Keywords (comma-separated)"
            value={keywords}
            onChange={(e) => setKeywords(e.target.value)}
          />
          <div className="flex gap-2">
            <Button onClick={handleCreate} disabled={submitting}>
              {submitting ? "Saving..." : "Add FAQ"}
            </Button>
            <Button variant="outline" onClick={load}>
              Refresh
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">FAQ Entries ({faqs.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : faqs.length === 0 ? (
            <p className="text-sm text-muted-foreground">No FAQs found.</p>
          ) : (
            <div className="space-y-3">
              {faqs.map((faq) => (
                <div key={faq.id} className="rounded-md border p-3">
                  <div className="mb-2 flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <Badge variant="outline">#{faq.id}</Badge>
                      <Badge variant="secondary">Used {faq.times_used}</Badge>
                    </div>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => handleDelete(faq.id)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                  <p className="text-sm font-medium">{faq.question}</p>
                  <p className="mt-1 text-sm text-muted-foreground">{faq.answer}</p>
                  <p className="mt-2 text-xs text-muted-foreground">
                    Guild: {faq.guild_id} • Keywords: {faq.match_keywords}
                  </p>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
