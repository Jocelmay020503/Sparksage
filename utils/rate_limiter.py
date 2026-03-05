from __future__ import annotations

import asyncio
import time
from collections import defaultdict, deque


class SlidingWindowRateLimiter:
    """In-memory sliding-window rate limiter (per 60 seconds)."""

    def __init__(self, window_seconds: int = 60):
        self.window_seconds = window_seconds
        self._user_events: dict[str, deque[float]] = defaultdict(deque)
        self._guild_events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    def _prune(self, events: deque[float], now: float) -> None:
        cutoff = now - self.window_seconds
        while events and events[0] < cutoff:
            events.popleft()

    async def check_and_record(
        self,
        user_id: str | None,
        guild_id: str | None,
        user_limit: int,
        guild_limit: int,
    ) -> tuple[bool, str | None]:
        """Check limits and record the event if allowed."""
        now = time.time()

        async with self._lock:
            if user_id:
                user_events = self._user_events[user_id]
                self._prune(user_events, now)
                if user_limit > 0 and len(user_events) >= user_limit:
                    retry_after = max(1, int(self.window_seconds - (now - user_events[0])))
                    return (
                        False,
                        f"⏳ You're sending requests too quickly. Please wait about {retry_after}s and try again.",
                    )

            if guild_id:
                guild_events = self._guild_events[guild_id]
                self._prune(guild_events, now)
                if guild_limit > 0 and len(guild_events) >= guild_limit:
                    retry_after = max(1, int(self.window_seconds - (now - guild_events[0])))
                    return (
                        False,
                        f"⏳ This server is currently rate-limited. Please wait about {retry_after}s and try again.",
                    )

            if user_id:
                self._user_events[user_id].append(now)
            if guild_id:
                self._guild_events[guild_id].append(now)

            return True, None

    async def get_quota_snapshot(self, top_n: int = 10) -> dict:
        """Return current per-minute usage snapshot for dashboard monitoring."""
        now = time.time()

        async with self._lock:
            for events in self._user_events.values():
                self._prune(events, now)
            for events in self._guild_events.values():
                self._prune(events, now)

            top_users = sorted(
                (
                    {"user_id": user_id, "requests_last_minute": len(events)}
                    for user_id, events in self._user_events.items()
                    if events
                ),
                key=lambda item: item["requests_last_minute"],
                reverse=True,
            )[:top_n]

            top_guilds = sorted(
                (
                    {"guild_id": guild_id, "requests_last_minute": len(events)}
                    for guild_id, events in self._guild_events.items()
                    if events
                ),
                key=lambda item: item["requests_last_minute"],
                reverse=True,
            )[:top_n]

            return {
                "window_seconds": self.window_seconds,
                "tracked_users": len([1 for events in self._user_events.values() if events]),
                "tracked_guilds": len([1 for events in self._guild_events.values() if events]),
                "top_users": top_users,
                "top_guilds": top_guilds,
            }


rate_limiter = SlidingWindowRateLimiter(window_seconds=60)
