import sqlite3

conn = sqlite3.connect("db.db")
cursor = conn.cursor()


# =========================
# TABLES
# =========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS battles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user1 TEXT,
    user2 TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS votes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    battle_id INTEGER,
    user_id INTEGER,
    vote TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS admins (
    user_id INTEGER PRIMARY KEY
)
""")

conn.commit()


# =========================
# BATTLES
# =========================
def create_battle(u1, u2):
    cursor.execute(
        "INSERT INTO battles (user1, user2) VALUES (?, ?)",
        (u1, u2)
    )
    conn.commit()
    return cursor.lastrowid


# =========================
# VOTES
# =========================
def add_vote(battle_id, user_id, vote):

    cursor.execute(
        "INSERT INTO votes (battle_id, user_id, vote) VALUES (?, ?, ?)",
        (battle_id, user_id, vote)
    )

    conn.commit()


def has_voted(battle_id, user_id):

    row = cursor.execute(
        "SELECT 1 FROM votes WHERE battle_id = ? AND user_id = ?",
        (battle_id, user_id)
    ).fetchone()

    return row is not None


# =========================
# ADMINS
# =========================
def add_admin(user_id):
    cursor.execute(
        "INSERT OR IGNORE INTO admins (user_id) VALUES (?)",
        (user_id,)
    )
    conn.commit()


def remove_admin(user_id):
    cursor.execute(
        "DELETE FROM admins WHERE user_id = ?",
        (user_id,)
    )
    conn.commit()


def get_admins():
    rows = cursor.execute("SELECT user_id FROM admins").fetchall()
    return [r[0] for r in rows]
