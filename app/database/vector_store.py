import json
import logging
import time
from datetime import datetime
from typing import Any, List, Optional, Tuple, Union

import google.generativeai as genai
import pandas as pd
import psycopg2
import psycopg2.extras
from config.settings import get_settings


class VectorStore:
    """Vector store backed by pgvector on PostgreSQL."""

    def __init__(self):
        self.settings = get_settings()
        genai.configure(api_key=self.settings.gemini.api_key)
        self.embedding_model = self.settings.gemini.embedding_model
        self.vector_settings = self.settings.vector_store
        self.conn = psycopg2.connect(self.settings.database.service_url)
        self.conn.autocommit = True

    def get_embedding(self, text: str) -> List[float]:
        """Generate embedding for the given text using Gemini."""
        text = text.replace("\n", " ")
        start_time = time.time()
        result = genai.embed_content(
            model=self.embedding_model,
            content=text,
            task_type="retrieval_document",
        )
        embedding = (
            result.get("embedding", result.get("values", []))
            if isinstance(result, dict)
            else getattr(result, "embedding", [])
        )
        logging.info("Embedding generated in %.3f seconds", time.time() - start_time)
        return embedding

    def create_tables(self) -> None:
        """Create required extensions and embeddings table."""
        with self.conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            cur.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self.vector_settings.table_name} (
                    id UUID PRIMARY KEY,
                    metadata JSONB NOT NULL,
                    contents TEXT NOT NULL,
                    embedding VECTOR({self.vector_settings.embedding_dimensions}) NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                """
            )

    def create_index(self) -> None:
        """Create IVFFLAT index for cosine similarity (safe to run repeatedly)."""
        with self.conn.cursor() as cur:
            cur.execute(
                f"""
                CREATE INDEX IF NOT EXISTS {self.vector_settings.table_name}_embedding_ivfflat
                ON {self.vector_settings.table_name}
                USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
                """
            )

    def drop_index(self) -> None:
        """Drop the embedding index."""
        with self.conn.cursor() as cur:
            cur.execute(
                f"DROP INDEX IF EXISTS {self.vector_settings.table_name}_embedding_ivfflat;"
            )

    def _to_vector_str(self, embedding: List[float]) -> str:
        """Convert embedding list to pgvector literal string."""
        return "[" + ",".join(f"{x:.8f}" for x in embedding) + "]"

    def upsert(self, df: pd.DataFrame) -> None:
        """
        Insert or update records in the database from a pandas DataFrame.

        Expected columns: id, metadata, contents, embedding
        """
        rows = []
        for _, row in df.iterrows():
            metadata = row["metadata"] or {}
            contents = row["contents"]
            embedding = row["embedding"]
            created_at = metadata.get("created_at")
            try:
                created_at_dt = (
                    datetime.fromisoformat(created_at)
                    if created_at
                    else datetime.utcnow()
                )
            except Exception:
                created_at_dt = datetime.utcnow()

            rows.append(
                (
                    row["id"],
                    json.dumps(metadata),
                    contents,
                    self._to_vector_str(embedding),
                    created_at_dt,
                )
            )

        with self.conn.cursor() as cur:
            insert_sql = f"""
                INSERT INTO {self.vector_settings.table_name}
                (id, metadata, contents, embedding, created_at)
                VALUES %s
                ON CONFLICT (id) DO UPDATE
                SET metadata = EXCLUDED.metadata,
                    contents = EXCLUDED.contents,
                    embedding = EXCLUDED.embedding,
                    created_at = EXCLUDED.created_at;
            """
            psycopg2.extras.execute_values(cur, insert_sql, rows)
        logging.info(
            "Inserted %d records into %s", len(df), self.vector_settings.table_name
        )

    def search(
        self,
        query_text: str,
        limit: int = 5,
        metadata_filter: Optional[dict] = None,
        time_range: Optional[Tuple[datetime, datetime]] = None,
        return_dataframe: bool = True,
    ) -> Union[List[Tuple[Any, ...]], pd.DataFrame]:
        """Query the vector database for similar embeddings using pgvector cosine distance."""
        query_embedding = self.get_embedding(query_text)
        vector_literal = self._to_vector_str(query_embedding)

        sql = f"""
            SELECT id,
                   metadata,
                   contents,
                   created_at,
                   (embedding <=> %s::vector) AS distance
            FROM {self.vector_settings.table_name}
        """
        params = [vector_literal]
        conditions = []

        if metadata_filter:
            conditions.append("metadata @> %s::jsonb")
            params.append(json.dumps(metadata_filter))

        if time_range:
            conditions.append("created_at BETWEEN %s AND %s")
            params.extend(time_range)

        if conditions:
            sql += " WHERE " + " AND ".join(conditions)

        sql += " ORDER BY embedding <=> %s::vector LIMIT %s"
        params.extend([vector_literal, limit])

        with self.conn.cursor() as cur:
            cur.execute(sql, params)
            results = cur.fetchall()

        if return_dataframe:
            return self._create_dataframe_from_results(results)
        return results

    def _create_dataframe_from_results(
        self,
        results: List[Tuple[Any, ...]],
    ) -> pd.DataFrame:
        """Create a pandas DataFrame from query results."""
        df = pd.DataFrame(
            results, columns=["id", "metadata", "contents", "created_at", "distance"]
        )

        # Expand metadata fields for convenience
        df = pd.concat(
            [df.drop(["metadata"], axis=1), df["metadata"].apply(pd.Series)], axis=1
        )
        df["id"] = df["id"].astype(str)
        return df

    def delete(
        self,
        ids: List[str] = None,
        metadata_filter: dict = None,
        delete_all: bool = False,
    ) -> None:
        """Delete records from the vector database."""
        if sum(bool(x) for x in (ids, metadata_filter, delete_all)) != 1:
            raise ValueError(
                "Provide exactly one of: ids, metadata_filter, or delete_all"
            )

        with self.conn.cursor() as cur:
            if delete_all:
                cur.execute(f"DELETE FROM {self.vector_settings.table_name};")
                logging.info(
                    "Deleted all records from %s", self.vector_settings.table_name
                )
            elif ids:
                cur.execute(
                    f"DELETE FROM {self.vector_settings.table_name} WHERE id = ANY(%s);",
                    (ids,),
                )
                logging.info(
                    "Deleted %d records from %s",
                    len(ids),
                    self.vector_settings.table_name,
                )
            elif metadata_filter:
                cur.execute(
                    f"DELETE FROM {self.vector_settings.table_name} WHERE metadata @> %s::jsonb;",
                    (json.dumps(metadata_filter),),
                )
                logging.info(
                    "Deleted records matching metadata filter from %s",
                    self.vector_settings.table_name,
                )
