import asyncio
import os

from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database import (
    add_user,
    create_battle,
    add_vote,
    has_voted,
    get_top,
    cursor,
    conn
)

# =========================
# CONFIG
# =========================
TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = 6287356721

bot = Bot(token=TOKEN)
dp = Dispatcher()

queue = []
admins = {OWNER_ID}

CHANNEL = "@mativstydio"


# =========================
# CHECK SUB
# =========================
async def check_sub(user_id: int):
    try:
        member = await bot.get_chat_member(CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False


# =========================
# ADMIN KEYBOARD
# =========================
def admin_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Users", callback_data="adm_users")],
        [InlineKeyboardButton(text="Top", callback_data="adm_top")],
        [InlineKeyboardButton(text="Stats", callback_data="adm_stats")],
        [InlineKeyboardButton(text="Clear votes", callback_data="adm_clear")]
    ])


# =========================
# START
# =========================
@dp.message(F.text == "/start")
async def start(msg: types.Message):

    uid = msg.from_user.id
    username = msg.from_user.username

    if not await check_sub(uid):
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Subscribe", url="https://t.me/mativstydio")]
        ])
        await msg.answer("Subscribe to use bot:", reply_markup=kb)
        return

    if not username:
        await msg.answer("No username")
        return

    add_user(uid, username)

    if username in queue:
        await msg.answer("Already in queue")
        return

    queue.append(username)
    await msg.answer("Added to queue")

    if len(queue) >= 2:
        u1 = queue.pop(0)
        u2 = queue.pop(0)

        battle_id = create_battle(u1, u2)

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="Player 1", callback_data=f"vote_{battle_id}_1"),
                InlineKeyboardButton(text="Player 2", callback_data=f"vote_{battle_id}_2")
            ]
        ])

        await msg.answer("BATTLE STARTED", reply_markup=kb)


# =========================
# VOTE
# =========================
@dp.callback_query(F.data.startswith("vote_"))
async def vote(call: types.CallbackQuery):

    uid = call.from_user.id

    _, battle_id, option = call.data.split("_")
    battle_id = int(battle_id)

    if has_voted(battle_id, uid):
        await call.answer("Already voted")
        return

    username = call.from_user.username or "unknown"

    add_vote(battle_id, uid, option + ":" + username)

    await call.answer("Vote counted")


# =========================
# ADMIN
# =========================
@dp.message(F.text == "/admin")
async def admin(msg: types.Message):

    if msg.from_user.id not in admins:
        await msg.answer("No access")
        return

    await msg.answer("Admin panel", reply_markup=admin_kb())


# =========================
# USERS
# =========================
@dp.callback_query(F.data == "adm_users")
async def users(call: types.CallbackQuery):

    data = cursor.execute("SELECT user_id, username FROM users").fetchall()

    text = "USERS:\n\n"

    for u in data[:30]:
        text += str(u[0]) + " | @" + str(u[1]) + "\n"

    await call.message.edit_text(text, reply_markup=admin_kb())


# =========================
# TOP
# =========================
@dp.callback_query(F.data == "adm_top")
async def top(call: types.CallbackQuery):

    data = get_top()

    text = "TOP:\n\n"

    for i, u in enumerate(data, 1):
        text += str(i) + ". @" + str(u[0]) + " - " + str(u[1]) + "\n"

    await call.message.edit_text(text, reply_markup=admin_kb())


# =========================
# STATS
# =========================
@dp.callback_query(F.data == "adm_stats")
async def stats(call: types.CallbackQuery):

    users = cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    battles = cursor.execute("SELECT COUNT(*) FROM battles").fetchone()[0]
    votes = cursor.execute("SELECT COUNT(*) FROM votes").fetchone()[0]

    text = "STATS:\n\nUsers: " + str(users) + "\nBattles: " + str(battles) + "\nVotes: " + str(votes)

    await call.message.edit_text(text, reply_markup=admin_kb())


# =========================
# CLEAR
# =========================
@dp.callback_query(F.data == "adm_clear")
async def clear(call: types.CallbackQuery):

    cursor.execute("DELETE FROM votes")
    conn.commit()

    await call.answer("Cleared")
    await call.message.edit_text("Votes cleared", reply_markup=admin_kb())


# =========================
# RUN
# =========================
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
