import aiosqlite
import random
import time

DB_PATH = "bot_data.db"

# Market rate — kept out of SQLite to avoid a rate-update race condition across connections
_current_rate = 1.0
_last_rate_update = 0

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "CREATE TABLE IF NOT EXISTS balances (user_id INTEGER PRIMARY KEY, amount INTEGER NOT NULL DEFAULT 0)"
        )
        await db.execute(
            "CREATE TABLE IF NOT EXISTS inventories ("
            "user_id INTEGER NOT NULL, item_name TEXT NOT NULL, base_value INTEGER NOT NULL)"
        )
        await db.commit()

async def get_balance(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT amount FROM balances WHERE user_id = ?", (user_id,)) as cur:
            row = await cur.fetchone()
            return row[0] if row else 0

async def add_balance(user_id, amount):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "INSERT INTO balances (user_id, amount) VALUES (?, ?) "
            "ON CONFLICT(user_id) DO UPDATE SET amount = amount + excluded.amount",
            (user_id, amount),
        ) as cur:
            await db.commit()
        async with db.execute("SELECT amount FROM balances WHERE user_id = ?", (user_id,)) as cur:
            row = await cur.fetchone()
            return row[0]

async def get_inventory(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT item_name, base_value FROM inventories WHERE user_id = ?", (user_id,)
        ) as cur:
            rows = await cur.fetchall()
        inventory = {}
        for item_name, base_value in rows:
            inventory.setdefault(item_name, []).append(base_value)
        return inventory

async def add_to_inventory(user_id, item_name, base_value):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO inventories (user_id, item_name, base_value) VALUES (?, ?, ?)",
            (user_id, item_name, base_value),
        )
        await db.commit()

async def remove_from_inventory(user_id, item_name, count=None):
    async with aiosqlite.connect(DB_PATH) as db:
        if count is None:
            async with db.execute(
                "SELECT base_value FROM inventories WHERE user_id = ? AND item_name = ?", (user_id, item_name)
            ) as cur:
                rows = await cur.fetchall()
            removed = [r[0] for r in rows]
            await db.execute(
                "DELETE FROM inventories WHERE user_id = ? AND item_name = ?", (user_id, item_name)
            )
        else:
            async with db.execute(
                "SELECT rowid, base_value FROM inventories WHERE user_id = ? AND item_name = ? LIMIT ?",
                (user_id, item_name, count),
            ) as cur:
                rows = await cur.fetchall()
            removed = [r[1] for r in rows]
            rowids = [r[0] for r in rows]
            if rowids:
                placeholders = ",".join("?" for _ in rowids)
                await db.execute(
                    f"DELETE FROM inventories WHERE rowid IN ({placeholders})", rowids
                )
        await db.commit()
        return removed

async def clear_inventory(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM inventories WHERE user_id = ?", (user_id,))
        await db.commit()

async def get_rate():
    global _current_rate, _last_rate_update
    now = time.time()
    if now - _last_rate_update >= 10:
        _current_rate = random.uniform(0.5, 2.0)
        _last_rate_update = now
    return _current_rate

async def set_rate(rate):
    global _current_rate
    _current_rate = rate