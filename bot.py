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
        [InlineKeyboardButton(text="👥 Пользователи", callback_data="adm_users")],
        [InlineKeyboardButton(text="🏆 Топ", callback_data="adm_top")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="adm_stats")],
        [InlineKeyboardButton(text="🗑 Очистить голоса", callback_data="adm_clear")]
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
            [InlineKeyboardButton(text="📢 Подписаться", url="https://t.me/mativstydio")],
            [InlineKeyboardButton(text="✅ Проверить", callback_data="check_sub")]
        ])

        await msg.answer(
            "👋 <b>Добро пожаловать!</b>\n\n"
            "📌 Подпишись на канал, чтобы использовать бота.",
            parse_mode="HTML",
            reply_markup=kb
        )
        return

    if not username:
        await msg.answer("❌ У тебя нет username в Telegram")
        return

    add_user(uid, username)

    if username in queue:
        await msg.answer("⏳ Ты уже в очереди")
        return

    queue.append(username)

    await msg.answer(f"✅ @{username} добавлен в очередь")

    # =========================
    # BATTLE
    # =========================
    if len(queue) >= 2:
        u1 = queue.pop(0)
        u2 = queue.pop(0)

        battle_id = create_battle(u1, u2)

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text=f"🔥 @{u1}", callback_data=f"vote_{battle_id}_1"),
                InlineKeyboardButton(text=f"⚔️ @{u2}", callback_data=f"vote_{battle_id}_2")
            ]
        ])

        await msg.answer(
            f"🔥 <b>БИТВА НАЧАЛАСЬ!</b>\n\n"
            f"⚔️ @{u1} VS @{u2}\n\n"
            "🗳 Голосуй за лучшего!",
            parse_mode="HTML",
            reply_markup=kb
        )


# =========================
# VOTE SYSTEM
# =========================
@dp.callback_query(F.data.startswith("vote_"))
async def vote(call: types.CallbackQuery):

    uid = call.from_user.id

    _, battle_id, option = call.data.split("_")
    battle_id = int(battle_id)

    if has_voted(battle_id, uid):
        await call.answer("❌ Ты уже голосовал за эту битву", show_alert=True)
        return

    username = call.from_user.username or "unknown"

    add_vote(battle_id, uid, f"{option}:{username}")

    await call.answer("✅ Голос засчитан")


# =========================
# CHECK SUB BUTTON
# =========================
@dp.callback_query(F.data == "check_sub")
async def check(call: types.CallbackQuery):

    if await check_sub(call.from_user.id):
        await call.message.edit_text("✅ Подписка подтверждена!")
    else:
        await call.answer("❌ Ты не подписан", show_alert=True)


# =========================
# ADMIN PANEL
# =========================
@dp.message(F.text == "/admin")
async def admin(msg: types.Message):

    if msg.from_user.id not in admins:
        await msg.answer("❌ Нет доступа")
        return

    await msg.answer(
        "👑 <b>АДМИН ПАНЕЛЬ</b>\n\nВыбери действие:",
        parse_mode="HTML",
        reply_markup=admin_kb()
    )


# =========================
# USERS
# =========================
@dp.callback_query(F.data == "adm_users")
async def users(call: types.CallbackQuery):

    data = cursor.execute("SELECT user_id, username FROM users").fetchall()

    text = "👥 <b>ПОЛЬЗОВАТЕЛИ</b>\n\n"

    for u in data[:30]:
        text += str(u[0]) + " | @" + str(u[1]) + "\n"

    await call.message.edit_text(text, parse_mode="HTML", reply_markup=admin_kb())


# =========================
# TOP
# =========================
@dp.callback_query(F.data == "adm_top")
async def top(call: types.CallbackQuery):

    data = get_top()

    text = "🏆 <b>ТОП</b>\n\n"

    for i, u in enumerate(data, 1):
        text += str(i) + ". @" + str(u[0]) + " — " + str(u[1]) + "\n"

    await call.message.edit_text(text, parse_mode="HTML", reply_markup=admin_kb())


# =========================
# STATS
# =========================
@dp.callback_query(F.data == "adm_stats")
async def stats(call: types.CallbackQuery):

    users = cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    battles = cursor.execute("SELECT COUNT(*) FROM battles").fetchone()[0]
    votes = cursor.execute("SELECT COUNT(*) FROM votes").fetchone()[0]

    text = (
        "📊 <b>СТАТИСТИКА</b>\n\n"
        "👥 Пользователи: " + str(users) + "\n"
        "⚔️ Битвы: " + str(battles) + "\n"
        "🗳 Голоса: " + str(votes)
    )

    await call.message.edit_text(text, parse_mode="HTML", reply_markup=admin_kb())


# =========================
# CLEAR VOTES
# =========================
@dp.callback_query(F.data == "adm_clear")
async def clear(call: types.CallbackQuery):

    cursor.execute("DELETE FROM votes")
    conn.commit()

    await call.answer("Очищено")
    await call.message.edit_text("🗑 Голоса очищены", reply_markup=admin_kb())


# =========================
# RUN
# =========================
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
