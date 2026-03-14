import os
import lancedb
from lancedb.pydantic import LanceModel, Vector
from pydantic import Field


# We use a simple 1536-dim vector for OpenAI's text-embedding-3-small/ada-002
class MistakeRecord(LanceModel):
    task: str
    error: str
    correction: str
    vector: Vector(1536) = Field(default_factory=lambda: [0.0] * 1536)


class MetaMemory:
    def __init__(self, db_path: str = ".aion_data/lancedb"):
        os.makedirs(db_path, exist_ok=True)
        self.db = lancedb.connect(db_path)
        self.table_name = "mistakes"

        if self.table_name not in self.db.table_names():
            self.table = self.db.create_table(self.table_name, schema=MistakeRecord)
        else:
            self.table = self.db.open_table(self.table_name)

    def record_mistake(self, task: str, error: str, correction: str):
        """Saves a failure to the vector DB to prevent future repetition."""
        record = MistakeRecord(
            task=task,
            error=error,
            correction=correction,
            # In production, integrate OpenAI embeddings here
            vector=[0.0] * 1536,
        )
        self.table.add([record])

    def find_similar_mistakes(self, task: str) -> list[str]:
        """Retrieves past corrections for similar tasks."""
        if self.table.count_rows() == 0:
            return []

        # In a real scenario, embed the `task` and search via vector.
        # For v0.0.1, we'll do a basic retrieval of recent mistakes.
        results = self.table.search([0.0] * 1536).limit(2).to_list()
        return [res["correction"] for res in results]
