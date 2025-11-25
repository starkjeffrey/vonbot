#!/usr/bin/env python3
"""Inspect legacy MSSQL database schema.

This script queries INFORMATION_SCHEMA to get table structures.
Run inside the legacy-adapter container.
"""

import sys

from app.database import get_connection


def inspect_table(table_name: str):
    """Get schema information for a table."""
    conn = get_connection()
    cursor = conn.cursor(as_dict=True)

    print(f"\n{'=' * 80}")
    print(f"Schema for table: {table_name}")
    print(f"{'=' * 80}\n")

    # Get column information
    cursor.execute(
        """
        SELECT
            COLUMN_NAME,
            DATA_TYPE,
            CHARACTER_MAXIMUM_LENGTH,
            IS_NULLABLE,
            COLUMN_DEFAULT
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = %s
        ORDER BY ORDINAL_POSITION
    """,
        (table_name,),
    )

    columns = cursor.fetchall()

    if not columns:
        print(f"❌ Table '{table_name}' not found or has no columns")
        cursor.close()
        conn.close()
        return

    # Print header
    print(f"{'Column Name':<40} {'Type':<20} {'Max Length':<12} {'Nullable':<10}")
    print("-" * 85)

    # Print columns
    for col in columns:
        col_name = col["COLUMN_NAME"]
        data_type = col["DATA_TYPE"]
        max_length = str(col["CHARACTER_MAXIMUM_LENGTH"]) if col["CHARACTER_MAXIMUM_LENGTH"] else "N/A"
        nullable = col["IS_NULLABLE"]

        print(f"{col_name:<40} {data_type:<20} {max_length:<12} {nullable:<10}")

    # Get row count
    cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
    count = cursor.fetchone()["count"]

    print(f"\n📊 Total Records: {count:,}")

    cursor.close()
    conn.close()


def list_tables():
    """List all tables in the database."""
    conn = get_connection()
    cursor = conn.cursor(as_dict=True)

    print(f"\n{'=' * 80}")
    print("Available Tables")
    print(f"{'=' * 80}\n")

    cursor.execute("""
        SELECT TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_NAME
    """)

    tables = cursor.fetchall()

    for idx, table in enumerate(tables, 1):
        print(f"{idx:3}. {table['TABLE_NAME']}")

    print(f"\n📊 Total Tables: {len(tables)}")

    cursor.close()
    conn.close()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        table_name = sys.argv[1]
        inspect_table(table_name)
    else:
        list_tables()
        print("\nUsage: python inspect_schema.py [table_name]")
        print("Example: python inspect_schema.py Students")
