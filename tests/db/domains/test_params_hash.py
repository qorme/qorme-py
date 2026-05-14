import sqlite3
import unittest

from qorme.context.tracking import QueryContext
from qorme.defaults import QORME_SETTINGS
from qorme.manager import TrackingManager


class ParamsHashTestCase(unittest.TestCase):
    """Tests for ParamsHash domain functionality using SQLite integration."""

    db_path = ":memory:"
    settings = {
        "domains": ["db.sqlite", "db.params_hash"],
        "db": {
            "sqlite": {"handler": "qorme.db.integrations.sqlite.SQLiteTracking"},
            "params_hash": {"handler": "qorme.db.domains.params_hash.ParamsHash"},
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
        manager.deps.events.register_sql_query_done_handler(self.query_executed_handler)

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

    def setup_test_data(self, conn):
        """Set up common test data for SELECT/UPDATE/DELETE tests."""
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                name TEXT,
                email TEXT,
                age INTEGER,
                active BOOLEAN,
                created_at TEXT
            )
        """)

        test_users = [
            (1, "Alice", "alice@example.com", 25, True, "2023-01-01"),
            (2, "Bob", "bob@example.com", 30, False, "2023-01-02"),
            (3, "Charlie", "charlie@example.com", 35, True, "2023-01-03"),
        ]
        for user in test_users:
            cursor.execute(
                "INSERT INTO users (id, name, email, age, active, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                user,
            )

        conn.commit()
        self.queries.clear()  # Clear setup queries

    def test_queries_without_parameters(self):
        """Test handling of queries with no parameters."""
        with self.context:
            conn = self.create_connection()
            self.setup_test_data(conn)
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM users")
            self.assertEqual(cursor.fetchone()[0], 3)

        # Should have 1 query
        self.assertEqual(len(self.queries), 1)
        query_data, _ = self.queries[0]
        self.assertEqual(query_data.params_hash, 17241709254077376921)

    def test_hash_only_set_for_select(self):
        with self.context:
            conn = self.create_connection()
            self.setup_test_data(conn)
            cursor = conn.cursor()

            # UPDATE
            cursor.execute(
                "UPDATE users SET name = ?, email = ? WHERE id = ?",
                ("Alice Updated", "alice.new@example.com", 1),
            )

            # DELETE
            cursor.execute(
                "DELETE FROM users WHERE age BETWEEN :min_age AND :max_age AND active = :status",
                {"min_age": 20, "max_age": 40, "status": False},
            )

        self.assertEqual(len(self.queries), 2)

        for query_data, _ in self.queries:
            self.assertIsNone(query_data.params_hash)

    def test_select_with_named_parameters(self):
        """Test SELECT statements with named parameters in WHERE clause."""
        with self.context:
            conn = self.create_connection()
            self.setup_test_data(conn)
            cursor = conn.cursor()

            # SELECT with named parameters
            cursor.execute(
                "SELECT * FROM users WHERE age > :min_age AND active = :is_active",
                {"min_age": 25, "is_active": True},
            )

        # Should have 1 query from the SELECT
        self.assertEqual(len(self.queries), 1)

        query_data, _ = self.queries[0]
        self.assertEqual(query_data.params_hash, 17776952373892114255)

    def test_select_with_in_clause(self):
        """Test SELECT with IN clause using list parameters."""
        with self.context:
            conn = self.create_connection()
            self.setup_test_data(conn)
            cursor = conn.cursor()

            # Note: SQLite doesn't support list parameters directly in IN clauses
            # So we use multiple positional parameters
            cursor.execute("SELECT * FROM users WHERE id IN (?, ?, ?)", (1, 2, 3))

        self.assertEqual(len(self.queries), 1)

        query_data, _ = self.queries[0]
        self.assertEqual(query_data.params_hash, 9771088612715187706)

    def test_complex_select_with_subquery(self):
        """Test complex SELECT with subquery and multiple parameter types."""
        with self.context:
            conn = self.create_connection()
            self.setup_test_data(conn)
            cursor = conn.cursor()

            # Complex query with subquery
            cursor.execute(
                """
                SELECT u.* FROM users u
                WHERE u.age > ?
                AND u.id IN (
                    SELECT id FROM users
                    WHERE created_at >= ? AND active = ?
                )
                ORDER BY u.name LIMIT ?
            """,
                (25, "2023-01-01", True, 10),
            )

        self.assertEqual(len(self.queries), 1)

        query_data, _ = self.queries[0]
        self.assertEqual(query_data.params_hash, 17330323401176943674)

    def test_null_and_special_values(self):
        """Test parameters with None, empty strings, and special values."""
        with self.context:
            conn = self.create_connection()
            self.setup_test_data(conn)
            cursor = conn.cursor()

            # SELECT with various special values
            cursor.execute(
                "SELECT * FROM users WHERE name != ? AND email IS NOT ? AND age >= ?", ("", None, 0)
            )

        self.assertEqual(len(self.queries), 1)

        query_data, _ = self.queries[0]
        self.assertEqual(query_data.params_hash, 15386407383426424308)
