import sqlite3

conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

# =========================
# 👥 USERS
# =========================
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT
)
""")


# =========================
# ⚔️ BATTLES
# =========================
cursor.execute("""
CREATE TABLE IF NOT EXISTS battles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user1 TEXT,
    user2 TEXT,
    active INTEGER DEFAULT 1
)
""")


# =========================
# 🗳️ VOTES
# =========================
cursor.execute("""
CREATE TABLE IF NOT EXISTS votes (
    battle_id INTEGER,
    user_id INTEGER,
    username TEXT
)
""")


# =========================
# 👑 ADMINS
# =========================
cursor.execute("""
CREATE TABLE IF NOT EXISTS admins (
    user_id INTEGER PRIMARY KEY
)
""")

conn.commit()


# =========================
# 👤 USERS
# =========================
def add_user(user_id: int, username: str):
    cursor.execute(
        "INSERT OR IGNORE INTO users VALUES (?, ?)",
        (user_id, username)
    )
    conn.commit()


def get_users():
    return cursor.execute("SELECT * FROM users").fetchall()


# =========================
# ⚔️ BATTLES
# =========================
def create_battle(u1: str, u2: str):
    cursor.execute(
        "INSERT INTO battles (user1, user2, active) VALUES (?, ?, 1)",
        (u1, u2)
    )
    conn.commit()
    return cursor.lastrowid


def get_active_battle():
    return cursor.execute(
        "SELECT * FROM battles WHERE active=1 ORDER BY id DESC LIMIT 1"
    ).fetchone()


def close_battle(battle_id: int):
    cursor.execute(
        "UPDATE battles SET active=0 WHERE id=?",
        (battle_id,)
    )
    conn.commit()


# =========================
# 🗳️ VOTES
# =========================
def add_vote(battle_id: int, user_id: int, username: str):
    cursor.execute(
        "INSERT INTO votes VALUES (?, ?, ?)",
        (battle_id, user_id, username)
    )
    conn.commit()


def has_voted(battle_id: int, user_id: int):
    return cursor.execute(
        "SELECT 1 FROM votes WHERE battle_id=? AND user_id=?",
        (battle_id, user_id)
    ).fetchone() is not None


def get_votes(battle_id: int):
    return cursor.execute(
        "SELECT username, COUNT(*) FROM votes WHERE battle_id=? GROUP BY username",
        (battle_id,)
    ).fetchall()


# =========================
# 👑 ADMINS
# =========================
def add_admin(user_id: int):
    cursor.execute(
        "INSERT OR IGNORE INTO admins VALUES (?)",
        (user_id,)
    )
    conn.commit()


def remove_admin(user_id: int):
    cursor.execute(
        "DELETE FROM admins WHERE user_id=?",
        (user_id,)
    )
    conn.commit()


def is_admin_db(user_id: int):
    return cursor.execute(
        "SELECT 1 FROM admins WHERE user_id=?",
        (user_id,)
    ).fetchone() is not None
    def add_admin(user_id):
    cursor.execute(
        "INSERT OR IGNORE INTO admins VALUES (?)",
        (user_id,)
    )
    conn.commit()


def is_admin(user_id):
    return cursor.execute(
        "SELECT 1 FROM admins WHERE user_id=?",
        (user_id,)
    ).fetchone()


def get_top():
    return cursor.execute("""
        SELECT username, COUNT(*) as votes
        FROM votes
        GROUP BY username
        ORDER BY votes DESC
        LIMIT 10
    """).fetchall()
    cursor.execute("""
CREATE TABLE IF NOT EXISTS admins (
    user_id INTEGER PRIMARY KEY
)
""")
conn.commit()
