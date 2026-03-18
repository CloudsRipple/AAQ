from __future__ import annotations

from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from phase0.config import load_config
from phase0.lanes import run_lane_cycle


class AuditAndMemoryPersistenceTests(unittest.TestCase):
    def test_writes_parameter_audit_and_memory_db(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            state_db = str(Path(tmpdir) / "state.db")
            memory_db = str(Path(tmpdir) / "memory.db")
            with patch.dict(
                "os.environ",
                {
                    "AI_STATE_DB_PATH": state_db,
                    "AI_MEMORY_DB_PATH": memory_db,
                    "AI_ENABLED": "true",
                    "LLM_BASE_URL": "http://127.0.0.1:1/v1",
                    "LLM_TIMEOUT_SECONDS": "0.2",
                    "LLM_MAX_RETRIES": "0",
                },
                clear=False,
            ):
                config = load_config()
                output = run_lane_cycle("AAPL", config=config)
            self.assertIn("low_async_processed", output)
            self.assertGreaterEqual(output["low_async_processed"], 1)
            with sqlite3.connect(state_db) as conn:
                rows = conn.execute("SELECT COUNT(*) FROM parameter_audit").fetchone()
            self.assertIsNotNone(rows)
            self.assertGreaterEqual(int(rows[0]), 1)
            with sqlite3.connect(memory_db) as conn:
                mem_rows = conn.execute("SELECT COUNT(*) FROM memory_records").fetchone()
            self.assertIsNotNone(mem_rows)
            self.assertGreaterEqual(int(mem_rows[0]), 1)


if __name__ == "__main__":
    unittest.main()
