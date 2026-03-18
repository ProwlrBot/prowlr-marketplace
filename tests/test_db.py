import sqlite3
import tempfile
import pathlib
import pytest
from api.db import init_db, record_download, get_stats

@pytest.fixture
def db_path(tmp_path):
    path = tmp_path / "test.db"
    init_db(path)
    return path

class TestDatabase:
    def test_init_creates_tables(self, db_path):
        conn = sqlite3.connect(db_path)
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        table_names = {t[0] for t in tables}
        assert "downloads" in table_names
        assert "download_counts" in table_names
        conn.close()

    def test_record_download(self, db_path):
        result = record_download(db_path, "skill-test", "abc123")
        assert result is True

    def test_record_download_dedup_same_day(self, db_path):
        record_download(db_path, "skill-test", "abc123")
        result = record_download(db_path, "skill-test", "abc123")
        assert result is False

    def test_record_download_different_listing(self, db_path):
        record_download(db_path, "skill-test", "abc123")
        result = record_download(db_path, "skill-other", "abc123")
        assert result is True

    def test_get_stats_empty(self, db_path):
        stats = get_stats(db_path, "skill-test")
        assert stats["total_downloads"] == 0
        assert stats["downloads_last_7_days"] == 0
        assert stats["downloads_last_30_days"] == 0

    def test_get_stats_after_download(self, db_path):
        record_download(db_path, "skill-test", "abc123")
        record_download(db_path, "skill-test", "def456")
        stats = get_stats(db_path, "skill-test")
        assert stats["total_downloads"] == 2
        assert stats["downloads_last_7_days"] == 2
        assert stats["downloads_last_30_days"] == 2
