from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import re
import sqlite3


@dataclass(frozen=True)
class MemoryRecord:
    memory_id: str
    tier: str
    text: str
    published_at: datetime
    tags: tuple[str, ...]


@dataclass(frozen=True)
class MemoryMatch:
    memory_id: str
    tier: str
    text: str
    published_at: str
    score: float


class LayeredMemoryStore:
    def __init__(self, records: list[MemoryRecord]) -> None:
        self._records = records
        self._vectors = {item.memory_id: _to_vector(item.text + " " + " ".join(item.tags)) for item in records}

    def query(
        self,
        query_text: str,
        now: datetime,
        limit: int = 4,
        tiers: tuple[str, ...] = ("short", "long", "relational"),
    ) -> list[MemoryMatch]:
        query_vec = _to_vector(query_text)
        ranked: list[tuple[MemoryRecord, float]] = []
        for record in self._records:
            if record.tier not in tiers:
                continue
            sim = _cosine(query_vec, self._vectors[record.memory_id])
            if sim <= 0:
                continue
            recency = _recency_weight(record.published_at, now)
            ranked.append((record, sim * recency))
        ranked.sort(key=lambda row: row[1], reverse=True)
        return [
            MemoryMatch(
                memory_id=record.memory_id,
                tier=record.tier,
                text=record.text,
                published_at=record.published_at.isoformat(),
                score=round(score, 4),
            )
            for record, score in ranked[:limit]
        ]


class PersistentLayeredMemoryStore(LayeredMemoryStore):
    def __init__(self, db_path: str, records: list[MemoryRecord]) -> None:
        self._db_path = db_path
        _ensure_memory_db(db_path)
        if records:
            _upsert_records(db_path, records)
        loaded = _load_records(db_path)
        super().__init__(loaded)

    @classmethod
    def from_db(cls, db_path: str) -> "PersistentLayeredMemoryStore":
        return cls(db_path=db_path, records=[])

    def upsert(self, records: list[MemoryRecord]) -> None:
        if not records:
            return
        _upsert_records(self._db_path, records)
        self._records = _load_records(self._db_path)
        self._vectors = {item.memory_id: _to_vector(item.text + " " + " ".join(item.tags)) for item in self._records}


def _ensure_memory_db(db_path: str) -> None:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS memory_records (
                memory_id TEXT PRIMARY KEY,
                tier TEXT NOT NULL,
                text TEXT NOT NULL,
                published_at TEXT NOT NULL,
                tags_json TEXT NOT NULL
            )
            """
        )
        conn.commit()


def _upsert_records(db_path: str, records: list[MemoryRecord]) -> None:
    with sqlite3.connect(db_path) as conn:
        for item in records:
            conn.execute(
                """
                INSERT INTO memory_records(memory_id, tier, text, published_at, tags_json)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(memory_id) DO UPDATE SET
                    tier=excluded.tier,
                    text=excluded.text,
                    published_at=excluded.published_at,
                    tags_json=excluded.tags_json
                """,
                (
                    item.memory_id,
                    item.tier,
                    item.text,
                    item.published_at.isoformat(),
                    json.dumps(list(item.tags), ensure_ascii=False),
                ),
            )
        conn.commit()


def _load_records(db_path: str) -> list[MemoryRecord]:
    _ensure_memory_db(db_path)
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT memory_id, tier, text, published_at, tags_json
            FROM memory_records
            ORDER BY published_at DESC
            """
        ).fetchall()
    result: list[MemoryRecord] = []
    for row in rows:
        tags_raw = json.loads(str(row[4]))
        tags = tuple(str(item) for item in tags_raw)
        result.append(
            MemoryRecord(
                memory_id=str(row[0]),
                tier=str(row[1]),
                text=str(row[2]),
                published_at=datetime.fromisoformat(str(row[3])),
                tags=tags,
            )
        )
    return result


def _to_vector(text: str) -> Counter[str]:
    tokens = re.findall(r"[a-zA-Z0-9\u4e00-\u9fff]+", text.lower())
    return Counter(tokens)


def _cosine(left: Counter[str], right: Counter[str]) -> float:
    if not left or not right:
        return 0.0
    dot = sum(left[token] * right.get(token, 0) for token in left)
    if dot <= 0:
        return 0.0
    norm_left = math.sqrt(sum(v * v for v in left.values()))
    norm_right = math.sqrt(sum(v * v for v in right.values()))
    if norm_left == 0 or norm_right == 0:
        return 0.0
    return dot / (norm_left * norm_right)


def _recency_weight(published_at: datetime, now: datetime) -> float:
    age_hours = max(0.0, (now - published_at.astimezone(timezone.utc)).total_seconds() / 3600)
    if age_hours <= 6:
        return 1.0
    if age_hours <= 24:
        return 0.9
    if age_hours <= 24 * 7:
        return 0.75
    if age_hours <= 24 * 30:
        return 0.55
    return 0.35
