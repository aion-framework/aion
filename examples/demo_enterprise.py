"""
Phase 3 proof of concept: Enterprise guardrails.

Demonstrates:
1. PIIScrubberPolicy: "admin@corp.com" is replaced with [REDACTED_PII] before the LLM.
2. Planner: agent breaks the goal into steps (e.g. "Verify Account XYZ", "Initiate Transfer").
3. HITL: transfer_funds tool calls suspend_for_approval; workflow pauses until an
   external approval event is sent to Hatchet (or timeout).

To resume after HITL pause: send an approval event to Hatchet with the matching
approval_key (e.g. approve_transfer_XYZ) and payload {"approved": true}.
"""

from dotenv import load_dotenv

from aion import AionAgent
from aion.middleware.policies import PIIScrubberPolicy
from aion.patterns import AionPlannerAgent

load_dotenv()


def main() -> None:
    agent = AionPlannerAgent(
        name="EnterpriseAgent",
        model="openai:gpt-4o-mini",
        system_prompt=(
            "You are a compliant financial assistant. When asked to transfer funds, "
            "use the transfer_funds(amount, account) tool. Break complex requests "
            "into clear steps: first verify the account, then initiate the transfer."
        ),
        policies=[PIIScrubberPolicy()],
    )
    # Email in the prompt will be scrubbed before planning; planner produces steps;
    # when the agent calls transfer_funds, the workflow will suspend for approval.
    event_id = agent.start(
        "My email is admin@corp.com. Please plan a transfer of $10,000 to account XYZ and execute it."
    )
    print(f"✅ Dispatched! Event ID: {event_id}")
    print("👉 Run `aion worker` in another terminal to process this task.")
    print("   When the worker hits transfer_funds, it will pause. Send an approval event to Hatchet to resume.")


if __name__ == "__main__":
    main()
