"""Tests for PostgreSQL connection tracking functionality."""

import os
import unittest
from datetime import datetime
from uuid import UUID

import psycopg2

from qorme.context.tracking import QueryContext
from qorme.db.datastructures import ConnectionData, TimeInterval
from qorme.db.integrations.psycopg2 import get_db_version
from qorme.db.types import DatabaseVendor
from qorme.defaults import QORME_SETTINGS
from qorme.manager import TrackingManager


class PostgreSQLTestCase(unittest.TestCase):
    """Tests for PostgreSQL connection tracking functionality using psycopg2."""

    settings = {
        "domains": ["db.psycopg2"],
        "db": {
            "psycopg2": {"handler": "qorme.db.integrations.psycopg2.Psycopg2Tracking"},
        },
    }

    # Collect database connection information from environment variables, falling
    # back to sane defaults that match the docker-compose set-up used in CI.
    _db_params = {
        "dbname": os.getenv("PG_NAME", "postgres"),
        "user": os.getenv("PG_USER", "postgres"),
        "password": os.getenv("PG_PASSWORD", "postgres"),
        "host": os.getenv("PG_HOST", "localhost"),
        "port": int(os.getenv("PG_PORT", 5454)),
    }

    def setUp(self):
        super().setUp()
        # Initialise tracking manager
        manager = TrackingManager(settings=self.settings, defaults=QORME_SETTINGS)
        self.manager = manager
        assert manager.start()

        # Lists populated via event hooks – used by assertions
        self.connections = []
        manager.deps.events.register_connection_created_handler(self.connection_created_handler)

        self.queries = []
        manager.deps.events.register_query_executed_handler(self.query_executed_handler)

        self.context = QueryContext(name="test_context", deps=manager.deps)

    def tearDown(self):
        # Close all opened connections
        for conn in self.connections:
            try:
                conn.close()
            except Exception:
                pass  # Ignore if already closed / error.
        self.manager.stop()
        super().tearDown()

    def create_connection(self):
        return psycopg2.connect(**self._db_params)

    def connection_created_handler(self, conn):
        self.connections.append(conn)

    def query_executed_handler(self, *args):
        self.queries.append(args)

    def assert_valid_tracker(self, conn):
        data = conn._self_data  # type: ignore[attr-defined]
        self.assertIsInstance(data, ConnectionData)
        self.assertIsInstance(data.uid, UUID)

        # Database information
        db = data.db
        self.assertEqual(db.vendor, DatabaseVendor.POSTGRESQL)
        self.assertEqual(db.name, self._db_params["dbname"])
        # Version should match the one obtained directly from the server
        expected_version = get_db_version(conn.__wrapped__)  # type: ignore[attr-defined]
        self.assertEqual(db.version, expected_version)

        # Creation interval
        creation = data.creation
        self.assertIsInstance(creation, TimeInterval)
        self.assertIsInstance(creation.start, datetime)
        self.assertIsInstance(creation.end, datetime)

    def test_creates_tracker_on_connect(self):
        """A connection tracker is created when connecting to PostgreSQL."""
        conn = self.create_connection()
        self.assert_valid_tracker(conn)

    def test_execute_tracking(self):
        """SQL execution is tracked along with parameters and results."""
        with self.context:
            conn = self.create_connection()
            cursor = conn.cursor()

            cursor.execute("CREATE TABLE IF NOT EXISTS test(id INTEGER, name TEXT)")
            cursor.execute("INSERT INTO test VALUES (%s, %s)", (1, "test"))
            cursor.execute("SELECT * FROM test")
            results = cursor.fetchall()
            self.assertEqual(results[-1], (1, "test"))

        # Three queries executed within context
        self.assertEqual(len(self.queries), 3)

        create_query, create_params = self.queries[0]
        self.assertIn("CREATE TABLE", create_query.sql.upper())
        self.assertIsNone(create_params)

        insert_query, insert_params = self.queries[1]
        self.assertIn("INSERT INTO", insert_query.sql.upper())
        self.assertEqual(insert_params, (1, "test"))

        select_query, select_params = self.queries[2]
        self.assertIn("SELECT", select_query.sql.upper())
        self.assertIsNone(select_params)

        # Context / connection linkage
        self.assertEqual(create_query.context_uid, self.context.data.uid)
        self.assertEqual(create_query.connection_uid, conn._self_data.uid)  # type: ignore[attr-defined]
        self.assertIsNotNone(create_query.time.start)
        self.assertIsNotNone(create_query.time.end)

    def test_executemany_tracking(self):
        """executemany() calls are properly tracked."""
        with self.context:
            conn = self.create_connection()
            cursor = conn.cursor()

            cursor.execute("CREATE TABLE IF NOT EXISTS test_many(id INTEGER, name TEXT)")
            params = [(1, "a"), (2, "b"), (3, "c")]
            cursor.executemany("INSERT INTO test_many VALUES (%s, %s)", params)

            cursor.execute("SELECT COUNT(*) FROM test_many")
            count = cursor.fetchone()[0]
            self.assertEqual(count, 3)

        # CREATE + executemany + SELECT
        self.assertEqual(len(self.queries), 3)

        executemany_query, executemany_params = self.queries[1]
        self.assertIn("INSERT INTO", executemany_query.sql.upper())
        self.assertEqual(executemany_params, params)

    def test_query_execution_without_context(self):
        """Queries executed outside of a QueryContext shouldn't be recorded."""
        conn = self.create_connection()
        cursor = conn.cursor()

        cursor.execute("CREATE TABLE IF NOT EXISTS test_noctx(id INTEGER)")
        cursor.execute("INSERT INTO test_noctx VALUES (1)")
        cursor.execute("SELECT COUNT(*) FROM test_noctx")
        self.assertEqual(cursor.fetchone()[0], 1)

        self.assertEqual(len(self.queries), 0)
