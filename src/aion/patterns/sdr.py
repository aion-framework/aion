"""
DurableSDR: Sales Development Representative agent pattern.

Includes find_lead_info, draft_outreach, and HITL-protected send_email.
"""

from __future__ import annotations

from aion import AionAgent, aion_tool
from aion.patterns.planner import AionPlannerAgent


@aion_tool
def find_lead_info(company_name: str) -> str:
    """Find lead/contact info for a company (mock)."""
    return f"Lead info for {company_name}: [CTO contact placeholder]"


@aion_tool
def draft_outreach(topic: str, recipient: str) -> str:
    """Draft an outreach email (mock)."""
    return f"Draft email to {recipient} re: {topic}"


async def send_email(to: str, subject: str, body: str) -> str:
    """Send email; requires human approval via HITL. Use get_aion_context().suspend_for_approval in worker."""
    from aion.core.context import get_aion_context
    ctx = get_aion_context()
    if ctx:
        await ctx.suspend_for_approval(f"approve_email_{to}", timeout="72h")
    return f"Sent to {to}: {subject}"


SYSTEM_PROMPT_SDR = (
    "You are a durable SDR agent. Use find_lead_info to look up contacts, "
    "draft_outreach to create emails, and send_email only after approval. "
    "Be concise and professional."
)


class DurableSDR(AionPlannerAgent):
    """
    Durable SDR (Sales Development Rep) agent with plan-and-execute and HITL send_email.
    """

    def __init__(
        self,
        name: str = "DurableSDR",
        model: str = "openai:gpt-4o-mini",
        system_prompt: str = "",
        **kwargs: object,
    ) -> None:
        super().__init__(
            name=name,
            model=model,
            system_prompt=system_prompt or SYSTEM_PROMPT_SDR,
            tools=[find_lead_info, draft_outreach],  # send_email registered in worker if needed
            **kwargs,
        )
