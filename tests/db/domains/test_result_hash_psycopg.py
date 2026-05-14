import os
import unittest

import psycopg

from qorme.context.tracking import QueryContext
from qorme.defaults import QORME_SETTINGS
from qorme.manager import TrackingManager


class ResultHashPsycopgTestCase(unittest.TestCase):
    """Tests for ResultHash domain functionality using psycopg (v3) integration."""

    # Collect database connection information from environment variables, falling
    # back to sane defaults that match the docker-compose set-up used in CI.
    _db_params = {
        "dbname": os.getenv("PG_NAME", "postgres"),
        "user": os.getenv("PG_USER", "postgres"),
        "password": os.getenv("PG_PASSWORD", "postgres"),
        "host": os.getenv("PG_HOST", "localhost"),
        "port": int(os.getenv("PG_PORT", 5454)),
    }

    settings = {
        "domains": ["db.psycopg", "db.result_hash"],
        "db": {
            "psycopg": {"handler": "qorme.db.integrations.psycopg.PsycopgTracking"},
            "result_hash": {
                "handler": "qorme.db.domains.result_hash.ResultHash",
                "driver": "psycopg",
            },
        },
    }

    test_users = [
        (1, "Alice", "alice@example.com", 25, True, 95.5, "2023-01-01"),
        (2, "Bob", "bob@example.com", 30, False, 87.2, "2023-01-02"),
        (3, "Charlie", "charlie@example.com", 35, True, 92.1, "2023-01-03"),
        (4, "Diana", "diana@example.com", 28, True, 98.7, "2023-01-04"),
    ]

    def setUp(self):
        super().setUp()
        # Set up tracking manager
        manager = TrackingManager(settings=self.settings, defaults=QORME_SETTINGS)
        self.manager = manager
        assert manager.start()

        self.connections = []
        manager.deps.events.register_connection_created_handler(self.connection_created_handler)

        self.queries = []
        manager.deps.events.register_sql_query_done_handler(self.query_executed_handler)

        self.result_hashes = {}  # Dict keyed by query UID
        manager.deps.events.register_sql_result_hash_computed_handler(
            self.result_hash_computed_handler
        )

        self.context = QueryContext(name="test_context", deps=manager.deps)

    def tearDown(self):
        # Clean up any connections created during tests
        for conn in self.connections:
            try:
                conn.close()
            except Exception:
                pass  # Already closed or error - ignore
        self.manager.stop()
        super().tearDown()

    def create_connection(self):
        return psycopg.connect(**self._db_params)

    def connection_created_handler(self, conn):
        self.connections.append(conn)

    def query_executed_handler(self, *args):
        self.queries.append(args)

    def result_hash_computed_handler(self, result_hash):
        self.result_hashes[result_hash.sql_query_uid] = result_hash.value

    def get_result_hash(self, query_index):
        query_data = self.queries[query_index][0]
        return self.result_hashes.get(query_data.uid)

    def setup_test_data(self, conn):
        """Set up common test data for testing."""
        num_queries = len(self.queries)
        cursor = conn.cursor()

        # Drop and recreate table to ensure clean state
        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                name TEXT,
                email TEXT,
                age INTEGER,
                active BOOLEAN,
                score REAL,
                created_at TEXT
            )
        """)

        for user in self.test_users:
            cursor.execute(
                "INSERT INTO users (id, name, email, age, active, score, created_at) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                user,
            )

        conn.commit()

        # Clear setup queries and their corresponding result hashes (if any)
        setup_queries = self.queries[num_queries:]
        for query_data, _ in setup_queries:
            # Remove any result hashes for setup queries
            if query_data.uid in self.result_hashes:
                del self.result_hashes[query_data.uid]

        self.queries[num_queries:] = []  # Clear setup queries

    def test_select_single_row_result_hash(self):
        """Test that result hash is computed for single row SELECT."""
        with self.context:
            conn = self.create_connection()
            self.setup_test_data(conn)
            cursor = conn.cursor()

            # SELECT single row
            cursor.execute("SELECT * FROM users WHERE id = %s", (1,))
            result = cursor.fetchone()
            cursor.close()

        # Verify query was tracked and has result hash
        self.assertEqual(len(self.queries), 1)
        query_data, params = self.queries[0]

        # Should have exact result_hash value from separate event
        result_hash = self.get_result_hash(0)
        self.assertEqual(result_hash, 11993205352533542676)

        # Result should be the expected row
        self.assertEqual(result, self.test_users[0])

    def test_select_multiple_rows_result_hash(self):
        """Test that result hash is computed for multiple row SELECT."""
        with self.context:
            conn = self.create_connection()
            self.setup_test_data(conn)
            cursor = conn.cursor()

            # SELECT multiple rows
            cursor.execute("SELECT name, age FROM users WHERE active = %s ORDER BY age", (True,))
            results = cursor.fetchall()
            cursor.close()

        self.assertEqual(len(self.queries), 1)
        query_data, params = self.queries[0]

        result_hash = self.get_result_hash(0)
        self.assertEqual(result_hash, 3549641319231524613)

        # Should have 3 active users
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0][0], "Alice")  # Youngest active user

    def test_empty_result_set_hash(self):
        """Test that result hash is computed even for empty result sets."""
        with self.context:
            conn = self.create_connection()
            self.setup_test_data(conn)
            cursor = conn.cursor()

            # SELECT with no matching rows
            cursor.execute("SELECT * FROM users WHERE age > %s", (100,))
            results = cursor.fetchall()

        self.assertEqual(len(self.queries), 1)
        query_data, params = self.queries[0]

        result_hash = self.get_result_hash(0)
        self.assertEqual(result_hash, 17241709254077376921)

        # Results should be empty
        self.assertEqual(len(results), 0)

    def test_fetchone_vs_fetchall_same_hash(self):
        """Test that fetchone and fetchall produce the same hash for the same query."""
        with self.context:
            conn = self.create_connection()
            self.setup_test_data(conn)
            cursor = conn.cursor()

            # First query with fetchone (single row)
            cursor.execute("SELECT * FROM users WHERE id = %s", (1,))
            cursor.fetchone()

            # Same query with fetchall (will get same single row)
            cursor.execute("SELECT * FROM users WHERE id = %s", (1,))
            cursor.fetchall()
            cursor.close()

        # Hashes should be identical for same data
        hash1 = self.get_result_hash(0)
        hash2 = self.get_result_hash(1)
        self.assertEqual(hash1, 11993205352533542676)
        self.assertEqual(hash1, hash2)

    def test_different_queries_different_hashes(self):
        """Test that different result sets produce different hashes."""
        with self.context:
            conn = self.create_connection()
            self.setup_test_data(conn)
            cursor = conn.cursor()

            # First query
            cursor.execute("SELECT * FROM users WHERE id = %s", (1,))
            cursor.fetchone()

            # Different query (different row)
            cursor.execute("SELECT * FROM users WHERE id = %s", (2,))
            cursor.fetchone()

            cursor.close()

        # Hashes should be different for different data
        hash1 = self.get_result_hash(0)
        hash2 = self.get_result_hash(1)
        self.assertEqual(hash1, 11993205352533542676)
        self.assertEqual(hash2, 4147941654976059549)
        self.assertNotEqual(hash1, hash2)

    def test_same_data_different_order_different_hashes(self):
        """Test that same data in different order produces different hashes."""
        with self.context:
            conn = self.create_connection()
            self.setup_test_data(conn)
            cursor = conn.cursor()

            # Query ordered by name
            cursor.execute("SELECT name, age FROM users WHERE active = %s ORDER BY name", (True,))
            cursor.fetchall()
            # Same data but ordered differently
            cursor.execute("SELECT name, age FROM users WHERE active = %s ORDER BY age", (True,))
            cursor.fetchall()

        # Different order should produce different hash
        hash1 = self.get_result_hash(0)
        hash2 = self.get_result_hash(1)
        self.assertEqual(hash1, 8702179705127943188)
        self.assertEqual(hash2, 3549641319231524613)
        self.assertNotEqual(hash1, hash2)

    def test_fetchmany_incremental_hashing(self):
        """Test that fetchmany calls accumulate hash correctly."""
        with self.context:
            conn = self.create_connection()
            self.setup_test_data(conn)
            cursor = conn.cursor()

            # Query all rows but fetch in batches
            cursor.execute("SELECT * FROM users ORDER BY id")
            batch1 = cursor.fetchmany(2)
            batch2 = cursor.fetchmany(2)
            cursor.close()

        self.assertEqual(len(self.queries), 1)
        # query_data = self.queries[0][0]
        result_hash = self.get_result_hash(0)
        self.assertEqual(result_hash, 2963662526920198971)

        # Should have fetched all 4 rows in batches
        self.assertEqual(len(batch1), 2)
        self.assertEqual(len(batch2), 2)

    def test_queries_without_fetch_no_hash(self):
        """Test that queries without fetch operations don't get result_hash."""
        with self.context:
            conn = self.create_connection()
            cursor = conn.cursor()

            # DDL operations don't fetch results
            cursor.execute("CREATE TABLE IF NOT EXISTS test (id INTEGER)")
            cursor.execute("INSERT INTO test VALUES (1)")
            cursor.execute("DROP TABLE test")
            cursor.close()

        # Should have 3 queries
        self.assertEqual(len(self.queries), 3)

        # None of these should have result_hash since no fetch occurred
        for i in range(3):
            result_hash = self.get_result_hash(i)
            self.assertIsNone(result_hash)

    def test_real_world_query_consistency(self):
        """Test that identical queries across connections produce same hash."""
        with self.context:
            conn = self.create_connection()
            self.setup_test_data(conn)
            cursor = conn.cursor()

            # First query
            cursor.execute("SELECT name, email FROM users WHERE active = %s ORDER BY id", (True,))
            result1 = cursor.fetchall()

            # Identical query again (should produce same data and hash)
            cursor.execute("SELECT name, email FROM users WHERE active = %s ORDER BY id", (True,))
            result2 = cursor.fetchall()
            cursor.close()

        # Results should be identical
        self.assertEqual(result1, result2)

        # Hashes should be identical for same data
        hash1 = self.get_result_hash(0)
        hash2 = self.get_result_hash(1)
        self.assertEqual(hash1, hash2)
        self.assertEqual(hash1, 16479753757390800353)
