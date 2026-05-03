import sqlite3

# =========================
# 📦 CONNECT DATABASE
# =========================
conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

# =========================
# 👤 USERS TABLE
# =========================
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT
)
""")

# =========================
# ⚔️ BATTLES TABLE
# =========================
cursor.execute("""
CREATE TABLE IF NOT EXISTS battles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user1 TEXT,
    user2 TEXT
)
""")

# =========================
# 🗳️ VOTES TABLE
# =========================
cursor.execute("""
CREATE TABLE IF NOT EXISTS votes (
    battle_id INTEGER,
    user_id INTEGER,
    username TEXT
)
""")

# =========================
# 👑 ADMINS TABLE
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
def add_user(user_id, username):
    cursor.execute(
        "INSERT OR IGNORE INTO users VALUES (?, ?)",
        (user_id, username)
    )
    conn.commit()

# =========================
# ⚔️ BATTLES
# =========================
def create_battle(u1, u2):
    cursor.execute(
        "INSERT INTO battles (user1, user2) VALUES (?, ?)",
        (u1, u2)
    )
    conn.commit()
    return cursor.lastrowid

# =========================
# 🗳️ VOTES
# =========================
def add_vote(battle_id, user_id, username):
    cursor.execute(
        "INSERT INTO votes VALUES (?, ?, ?)",
        (battle_id, user_id, username)
    )
    conn.commit()


def has_voted(battle_id, user_id):
    return cursor.execute(
        "SELECT 1 FROM votes WHERE battle_id=? AND user_id=?",
        (battle_id, user_id)
    ).fetchone() is not None

# =========================
# 👑 ADMINS
# =========================
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
    ).fetchone() is not None

# =========================
# 🏆 TOP USERS
# =========================
def get_top():
    return cursor.execute("""
        SELECT username, COUNT(*) as votes
        FROM votes
        GROUP BY username
        ORDER BY votes DESC
        LIMIT 10
    """).fetchall()
