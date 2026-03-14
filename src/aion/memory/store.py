"""
Vector memory store for the Aion Framework (Meta-Memory).

Embedded LanceDB with zero-config local tables. Stores mistake records
with OpenAI embeddings for similarity search so the agent can avoid
repeating the same errors.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import lancedb
from lancedb.pydantic import LanceModel, Vector

if TYPE_CHECKING:
    pass

# OpenAI text-embedding-3-small dimension
EMBEDDING_DIM = 1536


class MistakeRecord(LanceModel):
    """
    Schema for a single mistake stored in LanceDB.

    The vector field holds the embedding of task_context for similarity
    search so we can retrieve relevant past failures for a new task.
    """

    task_context: str
    error_trace: str
    correction_advice: str
    vector: Vector(EMBEDDING_DIM)


def _get_embedding(text: str) -> list[float]:
    """Produce an embedding for `text` using OpenAI."""
    from openai import OpenAI

    client = OpenAI()
    resp = client.embeddings.create(
        model="text-embedding-3-small",
        input=text,
    )
    return resp.data[0].embedding


class MetaMemory:
    """
    Local, zero-config vector store for agent mistakes.

    Uses LanceDB at `.aion_data/lancedb` to persist task_context,
    error_trace, and correction_advice with a vector index for
    similarity search.
    """

    def __init__(self, db_path: str = ".aion_data/lancedb") -> None:
        """
        Initialize the embedded LanceDB connection.

        Args:
            db_path: Directory for the LanceDB database.
        """
        os.makedirs(db_path, exist_ok=True)
        self._db = lancedb.connect(db_path)
        self._table_name = "mistakes"

        if self._table_name not in self._db.table_names():
            self._table = self._db.create_table(
                self._table_name,
                schema=MistakeRecord,
            )
        else:
            self._table = self._db.open_table(self._table_name)

    def save_mistake(
        self,
        task_context: str,
        error_trace: str,
        correction_advice: str,
    ) -> None:
        """
        Persist a mistake with an embedding of task_context for later search.

        Args:
            task_context: What the agent was trying to do.
            error_trace: The Python exception / stack trace.
            correction_advice: One-sentence instruction to avoid this next time.
        """
        vector = _get_embedding(task_context)
        record = MistakeRecord(
            task_context=task_context,
            error_trace=error_trace,
            correction_advice=correction_advice,
            vector=vector,
        )
        self._table.add([record])

    def get_warnings_for_task(self, current_task: str, limit: int = 2) -> list[str]:
        """
        Vector similarity search over past mistakes; return correction_advice.

        Args:
            current_task: The upcoming task (embedded and used as query).
            limit: Max number of past corrections to return.

        Returns:
            List of correction_advice strings to inject into the prompt.
        """
        if self._table.count_rows() == 0:
            return []

        query_vector = _get_embedding(current_task)
        results = (
            self._table.search(query_vector)
            .limit(limit)
            .to_list()
        )
        return [r["correction_advice"] for r in results]
