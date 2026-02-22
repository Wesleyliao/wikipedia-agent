"""Shared utilities."""

import time

import anthropic


def create_with_retries(
    client: anthropic.Anthropic,
    *,
    max_retries: int = 3,
    initial_delay: float = 3.0,
    **kwargs,
) -> anthropic.types.Message:
    """Call client.messages.create with exponential backoff retries."""
    delay = initial_delay
    for attempt in range(1, max_retries + 1):
        try:
            return client.messages.create(**kwargs)
        except (anthropic.APIStatusError, anthropic.APIConnectionError) as e:
            if attempt == max_retries:
                raise e
            print(f"Attempt {attempt} failed with {e}, retrying in {delay}s...")
            time.sleep(delay)
            delay *= 2
