import os
import sqlite3
import tempfile
import unittest
from datetime import datetime
from uuid import UUID

from qorme.context.tracking import QueryContext
from qorme.db.datastructures import ConnectionData, TimeInterval
from qorme.db.types import DatabaseVendor
from qorme.defaults import QORME_SETTINGS
from qorme.manager import TrackingManager


class SQLiteTestCase(unittest.TestCase):
    """Tests for SQLite connection tracking functionality."""

    db_path = ":memory:"
    settings = {
        "domains": ["db.sqlite"],
        "db": {
            "sqlite": {"handler": "qorme.db.integrations.sqlite.SQLiteTracking"},
        },
    }

    def setUp(self):
        super().setUp()

        # Set up tracking manager
        manager = TrackingManager(settings=self.settings, defaults=QORME_SETTINGS)
        self.manager = manager
        assert manager.start()

        self.connections = []
        manager.deps.events.register_connection_created_handler(self.connection_created_handler)

        self.queries = []
        manager.deps.events.register_query_executed_handler(self.query_executed_handler)

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

    def create_connection(self, db_path=db_path):
        return sqlite3.connect(db_path)

    def connection_created_handler(self, conn):
        self.connections.append(conn)

    def query_executed_handler(self, *args):
        self.queries.append(args)

    def assert_valid_tracker(self, conn, db_name=db_path):
        data = conn._self_data
        self.assertIsInstance(data, ConnectionData)
        self.assertIsInstance(data.uid, UUID)
        # Check database info
        db = data.db
        self.assertEqual(db.vendor, DatabaseVendor.SQLITE)
        self.assertEqual(db.name, db_name)
        self.assertEqual(db.version, sqlite3.sqlite_version)
        # Check creation time interval
        creation = data.creation
        self.assertIsInstance(creation, TimeInterval)
        self.assertIsInstance(creation.start, datetime)
        self.assertIsInstance(creation.end, datetime)

    def test_creates_tracker_on_connect(self):
        """Test that a connection tracker is created when connecting to SQLite."""
        db_path = tempfile.mktemp(suffix=".db")
        self.addCleanup(lambda: os.unlink(db_path) if os.path.exists(db_path) else None)

        conn = self.create_connection(db_path)
        self.assert_valid_tracker(conn, db_path)

    def test_execute_tracking(self):
        """Test that SQL query execution is tracked."""
        with self.context:
            conn = self.create_connection()
            cursor = conn.cursor()

            # Execute some SQL commands
            cursor.execute("CREATE TABLE test (id INTEGER, name TEXT)")
            cursor.execute("INSERT INTO test VALUES (?, ?)", (1, "test"))
            cursor.execute("SELECT * FROM test")
            results = cursor.fetchall()
            self.assertEqual(results, [(1, "test")])

        self.assertEqual(len(self.queries), 3)

        # Validate each query: (query_data, params, result)
        create_query, create_params = self.queries[0]
        self.assertIn("CREATE TABLE test", create_query.sql)
        self.assertIsNone(create_params)

        insert_query, insert_params = self.queries[1]
        self.assertIn("INSERT INTO test VALUES", insert_query.sql)
        self.assertEqual(insert_params, (1, "test"))

        select_query, select_params = self.queries[2]
        self.assertIn("SELECT * FROM test", select_query.sql)
        self.assertIsNone(select_params)

        # Validate query_data structure (all should have same context/connection)
        self.assertEqual(create_query.context_uid, self.context.data.uid)
        self.assertEqual(create_query.connection_uid, conn._self_data.uid)
        self.assertIsNotNone(create_query.time.start)
        self.assertIsNotNone(create_query.time.end)

    def test_executemany_tracking(self):
        """Test that executemany is properly tracked."""
        with self.context:
            cursor = self.create_connection().cursor()

            cursor.execute("CREATE TABLE test (id INTEGER, name TEXT)")
            cursor.executemany(
                "INSERT INTO test VALUES (?, ?)", [(1, "test1"), (2, "test2"), (3, "test3")]
            )

            cursor.execute("SELECT COUNT(*) FROM test")
            count = cursor.fetchone()[0]
            self.assertEqual(count, 3)

        self.assertEqual(len(self.queries), 3)  # CREATE + executemany + SELECT

        # Validate executemany query specifically
        executemany_query, executemany_params = self.queries[1]
        self.assertIn("INSERT INTO test VALUES", executemany_query.sql)
        self.assertEqual(executemany_params, [(1, "test1"), (2, "test2"), (3, "test3")])

        # Validate COUNT query result
        count_query, count_params = self.queries[2]
        self.assertIn("SELECT COUNT(*)", count_query.sql)
        self.assertIsNone(count_params)

    def test_query_execution_without_context(self):
        """Test that queries without context don't break."""
        cursor = self.create_connection().cursor()

        # No context manager used
        cursor.execute("CREATE TABLE test (id INTEGER)")
        cursor.execute("INSERT INTO test VALUES (1)")
        cursor.execute("SELECT COUNT(*) FROM test")
        self.assertEqual(cursor.fetchone()[0], 1)

        self.assertEqual(len(self.queries), 0)
