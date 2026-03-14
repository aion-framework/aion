"""
Exception catcher for the Aion Framework.

Analyzes tool/agent failures via a lightweight LLM call and stores
them in MetaMemory so retries can avoid the same mistake.
"""

from __future__ import annotations

import traceback
from typing import TYPE_CHECKING

from openai import OpenAI

if TYPE_CHECKING:
    from aion.memory.store import MetaMemory

_CORRECTION_PROMPT = """The AI agent was trying to do: {task_context}. It encountered this Python error: {error_trace}. Write a 1-sentence instruction on how the agent should format its output or change its behavior to avoid this next time. Reply with only that one sentence, no preamble."""


class ExceptionAnalyzer:
    """
    Analyzes exceptions with a fast LLM call and persists the result
    in MetaMemory for prompt injection on retry.
    """

    def __init__(
        self,
        memory: MetaMemory | None = None,
        model: str = "gpt-4o-mini",
    ) -> None:
        """
        Args:
            memory: MetaMemory instance; if None, a default is created.
            model: Model used for the correction summary.
        """
        from aion.memory.store import MetaMemory as MetaMemoryCls

        self._memory = memory or MetaMemoryCls()
        self._model = model
        self._client = OpenAI()

    async def analyze_and_store(self, task_context: str, exception: Exception) -> None:
        """
        Ask the LLM for a one-sentence correction, then save to MetaMemory.

        Args:
            task_context: What the agent was trying to do.
            exception: The exception that was raised.
        """
        error_trace = traceback.format_exc()
        prompt = _CORRECTION_PROMPT.format(
            task_context=task_context,
            error_trace=error_trace,
        )
        resp = self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
        )
        correction_advice = (resp.choices[0].message.content or "").strip()
        if not correction_advice:
            correction_advice = f"Avoid the action that caused: {exception!s}"

        self._memory.save_mistake(
            task_context=task_context,
            error_trace=error_trace,
            correction_advice=correction_advice,
        )
