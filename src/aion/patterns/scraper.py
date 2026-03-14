"""
DurableWebScraper: production-ready durable agent pattern for data extraction.

Pre-built for web scraping and structured data extraction with
fetch_url_content and extract_structured_data tools.
"""

from __future__ import annotations

from aion import AionAgent, aion_tool


@aion_tool
def fetch_url_content(url: str) -> str:
    """Fetch the raw text content from a URL (mock implementation)."""
    return f"[Mock content from {url}]"


@aion_tool
def extract_structured_data(raw_text: str, schema_hint: str) -> str:
    """Extract structured data from raw text according to a schema hint (mock)."""
    return f"Extracted data for schema: {schema_hint}"


SYSTEM_PROMPT_SCRAPER = (
    "You are a durable web scraping agent. Use fetch_url_content to get page content, "
    "then use extract_structured_data to produce structured output. Always confirm URLs before fetching."
)


class DurableWebScraper(AionAgent):
    """Durable agent pattern optimized for data extraction and web scraping."""

    def __init__(
        self,
        name: str = "DurableWebScraper",
        model: str = "openai:gpt-4o-mini",
        system_prompt: str = "",
        **kwargs: object,
    ) -> None:
        super().__init__(
            name=name,
            model=model,
            system_prompt=system_prompt or SYSTEM_PROMPT_SCRAPER,
            tools=[fetch_url_content, extract_structured_data],
            **kwargs,
        )
