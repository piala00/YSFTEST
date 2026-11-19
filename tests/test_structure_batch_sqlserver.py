"""Regression tests for batched SQL Server structure introspection."""
import unittest
from unittest.mock import MagicMock, patch

from apps.core import structure_base


class BatchColumnMetadataTests(unittest.TestCase):
    @patch.object(structure_base, "connection")
    def test_non_sql_server_uses_existing_introspection(self, connection):
        connection.vendor = "sqlite"
        self.assertEqual(structure_base._colonnes_sql_server({"foo"}), {})
        connection.cursor.assert_not_called()

    @patch.object(structure_base, "connection")
    def test_batch_and_ambiguous_schema_fallback(self, connection):
        connection.vendor = "microsoft"
        cursor = MagicMock()
        cursor.fetchall.side_effect = [
            [("agency", "id"), ("agency", "Name"), ("duplicate", "id"),
             ("duplicate", "other")],
            [("agency",), ("duplicate",), ("duplicate",)],
        ]
        connection.cursor.return_value.__enter__.return_value = cursor
        self.assertEqual(
            structure_base._colonnes_sql_server({"agency", "duplicate"}),
            {"agency": {"id", "name"}},
        )
        self.assertEqual(cursor.execute.call_count, 2)


if __name__ == "__main__":
    unittest.main()
