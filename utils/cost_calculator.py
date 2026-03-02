"""
Cost calculation utilities for tracking API usage expenses.

Providers store pricing per million tokens or per thousand tokens.
This module handles conversion and calculation.
"""

from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class ProviderPricing:
    """Pricing for a single AI provider model."""
    name: str
    model: str
    input_cost_per_1k: float  # Cost per 1,000 input tokens
    output_cost_per_1k: float  # Cost per 1,000 output tokens


# Provider pricing as of 2026-03 (in USD)
# Updated pricing based on official provider rates
PROVIDER_PRICING: Dict[str, ProviderPricing] = {
    "gemini": ProviderPricing(
        name="Gemini",
        model="gemini-2.0-flash",
        input_cost_per_1k=0.075 / 1000,  # $0.075 per million
        output_cost_per_1k=0.3 / 1000,   # $0.3 per million
    ),
    "groq": ProviderPricing(
        name="Groq",
        model="mixtral-8x7b-32768",
        input_cost_per_1k=0.0,   # Free tier during beta
        output_cost_per_1k=0.0,  # Free tier during beta
    ),
    "openrouter": ProviderPricing(
        name="OpenRouter",
        model="mixtral-8x7b",
        input_cost_per_1k=0.27 / 1000,   # $0.27 per million
        output_cost_per_1k=0.81 / 1000,  # $0.81 per million
    ),
    "anthropic": ProviderPricing(
        name="Anthropic",
        model="claude-3-haiku",
        input_cost_per_1k=0.25 / 1000,   # $0.25 per million
        output_cost_per_1k=1.25 / 1000,  # $1.25 per million
    ),
    "openai": ProviderPricing(
        name="OpenAI",
        model="gpt-4o-mini",
        input_cost_per_1k=0.075 / 1000,   # $0.075 per million
        output_cost_per_1k=0.3 / 1000,    # $0.3 per million
    ),
}


def get_provider_pricing(provider: str) -> Optional[ProviderPricing]:
    """Get pricing for a provider."""
    return PROVIDER_PRICING.get(provider.lower())


def calculate_cost(
    provider: str,
    input_tokens: int = 0,
    output_tokens: int = 0,
) -> float:
    """
    Calculate cost in USD for a provider's token usage.
    
    Args:
        provider: Provider name (gemini, groq, etc.)
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        
    Returns:
        Cost in USD, rounded to 6 decimal places
    """
    pricing = get_provider_pricing(provider)
    if not pricing:
        return 0.0

    input_cost = (input_tokens / 1000) * pricing.input_cost_per_1k
    output_cost = (output_tokens / 1000) * pricing.output_cost_per_1k
    total_cost = input_cost + output_cost
    
    return round(total_cost, 6)


def format_cost(cost: float) -> str:
    """Format cost for display."""
    if cost >= 1.0:
        return f"${cost:.2f}"
    elif cost >= 0.001:
        return f"${cost * 1000:.2f}m"  # millidollars
    else:
        return f"${cost * 1000000:.2f}µ"  # microdollars


def get_all_provider_costs() -> Dict[str, ProviderPricing]:
    """Get pricing for all configured providers."""
    return PROVIDER_PRICING.copy()
