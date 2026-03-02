"""Rate limiting utilities for SparkSage.

Implements a sliding window rate limiter to prevent abuse and manage provider quotas.
Tracks per-user and per-guild usage with configurable limits.
"""

import time
from collections import defaultdict
from typing import Tuple


class RateLimiter:
    """Sliding window rate limiter for tracking usage per user and guild."""

    def __init__(self, user_limit: int = 30, user_window: int = 60, 
                 guild_limit: int = 300, guild_window: int = 60):
        """
        Initialize rate limiter with per-user and per-guild limits.
        
        Args:
            user_limit: Maximum requests per user in the time window
            user_window: Time window in seconds for user limit (default 60s = 1 min)
            guild_limit: Maximum requests per guild in the time window
            guild_window: Time window in seconds for guild limit (default 60s = 1 min)
        """
        self.user_limit = user_limit
        self.user_window = user_window
        self.guild_limit = guild_limit
        self.guild_window = guild_window

        # Track request timestamps: {user_id: [timestamp1, timestamp2, ...], ...}
        self.user_requests: dict[str, list[float]] = defaultdict(list)
        # Track guild timestamps: {guild_id: [timestamp1, timestamp2, ...], ...}
        self.guild_requests: dict[str, list[float]] = defaultdict(list)

    def _cleanup_old_requests(self, requests: list[float], window: int) -> list[float]:
        """Remove requests older than the window."""
        now = time.time()
        # Keep only requests within the window
        return [ts for ts in requests if now - ts < window]

    def check_user_limit(self, user_id: str) -> Tuple[bool, int, int]:
        """
        Check if a user has exceeded their rate limit.
        
        Args:
            user_id: Discord user ID as string
            
        Returns:
            Tuple of (is_allowed, remaining_requests, reset_in_seconds)
            - is_allowed: True if user is within limit
            - remaining_requests: Number of requests left in current window
            - reset_in_seconds: Seconds until next request is allowed (0 if allowed)
        """
        now = time.time()
        # Clean up old requests
        self.user_requests[user_id] = self._cleanup_old_requests(
            self.user_requests[user_id], self.user_window
        )
        
        requests = self.user_requests[user_id]
        
        if len(requests) < self.user_limit:
            # Under limit, allow request
            requests.append(now)
            remaining = self.user_limit - len(requests)
            return True, remaining, 0
        else:
            # At limit, check if oldest request is old enough
            oldest_request = min(requests)
            time_until_reset = self.user_window - (now - oldest_request)
            
            if time_until_reset <= 0:
                # Old request is outside window, allow new request
                requests.append(now)
                remaining = self.user_limit - len(requests)
                return True, remaining, 0
            else:
                # Still in window, deny request
                return False, 0, int(time_until_reset) + 1

    def check_guild_limit(self, guild_id: str) -> Tuple[bool, int, int]:
        """
        Check if a guild has exceeded their rate limit.
        
        Args:
            guild_id: Discord guild ID as string
            
        Returns:
            Tuple of (is_allowed, remaining_requests, reset_in_seconds)
            - is_allowed: True if guild is within limit
            - remaining_requests: Number of requests left in current window
            - reset_in_seconds: Seconds until next request is allowed (0 if allowed)
        """
        now = time.time()
        # Clean up old requests
        self.guild_requests[guild_id] = self._cleanup_old_requests(
            self.guild_requests[guild_id], self.guild_window
        )
        
        requests = self.guild_requests[guild_id]
        
        if len(requests) < self.guild_limit:
            # Under limit, allow request
            requests.append(now)
            remaining = self.guild_limit - len(requests)
            return True, remaining, 0
        else:
            # At limit, check if oldest request is old enough
            oldest_request = min(requests)
            time_until_reset = self.guild_window - (now - oldest_request)
            
            if time_until_reset <= 0:
                # Old request is outside window, allow new request
                requests.append(now)
                remaining = self.guild_limit - len(requests)
                return True, remaining, 0
            else:
                # Still in window, deny request
                return False, 0, int(time_until_reset) + 1

    def check_both_limits(self, user_id: str, guild_id: str | None) -> Tuple[bool, str]:
        """
        Check both user and guild limits.
        
        Args:
            user_id: Discord user ID as string
            guild_id: Discord guild ID as string (None for DMs)
            
        Returns:
            Tuple of (is_allowed, reason)
            - is_allowed: True if both limits are satisfied
            - reason: Empty string if allowed, otherwise error message
        """
        # Check user limit first
        user_allowed, user_remaining, user_reset = self.check_user_limit(user_id)
        if not user_allowed:
            return False, (
                f"⏱️ You're using SparkSage too frequently. "
                f"Please wait {user_reset} second(s) before trying again."
            )
        
        # Check guild limit if in a guild
        if guild_id:
            guild_allowed, guild_remaining, guild_reset = self.check_guild_limit(guild_id)
            if not guild_allowed:
                return False, (
                    f"⏱️ This server is using SparkSage too frequently. "
                    f"Please wait {guild_reset} second(s) before trying again."
                )
        
        return True, ""

    def get_user_status(self, user_id: str) -> dict:
        """Get current rate limit status for a user."""
        self.user_requests[user_id] = self._cleanup_old_requests(
            self.user_requests[user_id], self.user_window
        )
        requests_count = len(self.user_requests[user_id])
        return {
            "user_id": user_id,
            "requests_in_window": requests_count,
            "limit": self.user_limit,
            "remaining": max(0, self.user_limit - requests_count),
            "window_seconds": self.user_window,
        }

    def get_guild_status(self, guild_id: str) -> dict:
        """Get current rate limit status for a guild."""
        self.guild_requests[guild_id] = self._cleanup_old_requests(
            self.guild_requests[guild_id], self.guild_window
        )
        requests_count = len(self.guild_requests[guild_id])
        return {
            "guild_id": guild_id,
            "requests_in_window": requests_count,
            "limit": self.guild_limit,
            "remaining": max(0, self.guild_limit - requests_count),
            "window_seconds": self.guild_window,
        }

    def reset_user(self, user_id: str):
        """Reset rate limit for a user (admin only)."""
        self.user_requests[user_id] = []

    def reset_guild(self, guild_id: str):
        """Reset rate limit for a guild (admin only)."""
        self.guild_requests[guild_id] = []

    def reset_all(self):
        """Reset all rate limits (admin only)."""
        self.user_requests.clear()
        self.guild_requests.clear()
