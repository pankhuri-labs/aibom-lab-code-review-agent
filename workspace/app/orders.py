import sqlite3


def find_order(conn: sqlite3.Connection, order_id: str):
    return conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
