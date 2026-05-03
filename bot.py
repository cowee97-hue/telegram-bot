import asyncio
import os

from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database import (
    add_user,
    create_battle,
    add_vote,
    has_voted,
    is_admin,
    add_admin,
    get_top,
    cursor,
    conn
)

# =========================
# ⚙️ НАСТРОЙКИ
# =========================
TOKEN = os.getenv("BOT_TOKEN")

OWNER_ID = 6287356721
CHANNEL = "@mativstydio"

bot = Bot(token=TOKEN)
dp = Dispatcher()

queue = []

# =========================
# 🔐 ADMIN SYSTEM
# =========================
admin_sessions = {}
ADMIN_PASSWORD = "6767"


def is_admin_full(user_id):
    return user_id == OWNER_ID or is_admin(user_id)


def admin_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Пользователи", callback_data="users_0")],
        [InlineKeyboardButton(text="🏆 Топ", callback_data="top")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton(text="⚔️ Битвы", callback_data="battles")],
        [InlineKeyboardButton(text="➕ Админ", callback_data="add_admin")],
        [InlineKeyboardButton(text="🚪 Выход", callback_data="logout")]
    ])


# =========================
# 📢 ПОДПИСКА
# =========================
async def check_sub(user_id: int):
    try:
        member = await bot.get_chat_member(CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False


# =========================
# 🚀 START
# =========================
@dp.message(F.text == "/start")
async def start(msg: types.Message):

    user_id = msg.from_user.id
    username = msg.from_user.username

    if not await check_sub(user_id):
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Подписаться", url="https://t.me/mativstydio")],
            [InlineKeyboardButton(text="✅ Я подписался", callback_data="check_sub")]
        ])
        await msg.answer("❗ Подпишись на канал:", reply_markup=kb)
        return

    if not username:
        await msg.answer("❌ Нужен username")
        return

    add_user(user_id, username)

    if username in queue:
        await msg.answer("⏳ Ты уже в очереди")
        return

    queue.append(username)
    await msg.answer(f"✅ @{username} добавлен")

    if len(queue) >= 2:
        u1 = queue.pop(0)
        u2 = queue.pop(0)

        battle_id = create_battle(u1, u2)

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text=f"🔥 @{u1} (0)", callback_data=f"vote_{battle_id}_{u1}"),
                InlineKeyboardButton(text=f"⚔️ @{u2} (0)", callback_data=f"vote_{battle_id}_{u2}")
            ]
        ])

        await msg.answer(f"🔥 БИТВА!\n@{u1} VS @{u2}", reply_markup=kb)


# =========================
# 🔐 ADMIN LOGIN
# =========================
@dp.message(F.text == "/admin")
async def admin_login(msg: types.Message):
    admin_sessions[msg.from_user.id] = "password"
    await msg.answer("🔐 Введи пароль:")


# =========================
# 🧠 ADMIN INPUT (ОДИН!)
# =========================
@dp.message()
async def admin_input(msg: types.Message):
    user_id = msg.from_user.id
    state = admin_sessions.get(user_id)

    if state == "password":
        if msg.text == ADMIN_PASSWORD:
            admin_sessions[user_id] = "menu"
            await msg.answer("👑 Админ панель", reply_markup=admin_kb())
        else:
            admin_sessions.pop(user_id, None)
            await msg.answer("❌ Неверный пароль")

    elif state == "add_admin":
        try:
            add_admin(int(msg.text))
            admin_sessions[user_id] = "menu"
            await msg.answer("✅ Админ добавлен", reply_markup=admin_kb())
        except:
            await msg.answer("❌ Ошибка")


# =========================
# 👥 USERS (страницы)
# =========================
@dp.callback_query(F.data.startswith("users_"))
async def users(call: types.CallbackQuery):
    if not is_admin_full(call.from_user.id):
        return

    page = int(call.data.split("_")[1])
    users = cursor.execute("SELECT user_id, username FROM users").fetchall()

    per_page = 5
    start = page * per_page
    end = start + per_page

    kb = []

    for u in users[start:end]:
        kb.append([InlineKeyboardButton(
            text=f"@{u[1]}",
            callback_data=f"user_{u[0]}"
        )])

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"users_{page-1}"))
    if end < len(users):
        nav.append(InlineKeyboardButton(text="➡️", callback_data=f"users_{page+1}"))

    if nav:
        kb.append(nav)

    kb.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back")])

    await call.message.edit_text("👥 Пользователи:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))


# =========================
# 👤 USER DETAIL
# =========================
@dp.callback_query(F.data.startswith("user_"))
async def user_detail(call: types.CallbackQuery):
    uid = int(call.data.split("_")[1])

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Удалить", callback_data=f"del_{uid}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="users_0")]
    ])

    await call.message.edit_text(f"👤 ID: {uid}", reply_markup=kb)


# =========================
# ❌ DELETE USER
# =========================
@dp.callback_query(F.data.startswith("del_"))
async def delete_user(call: types.CallbackQuery):
    uid = int(call.data.split("_")[1])

    cursor.execute("DELETE FROM users WHERE user_id=?", (uid,))
    conn.commit()

    await call.answer("Удалён")
    await call.message.edit_text("✅ Удалён", reply_markup=admin_kb())


# =========================
# 🏆 TOP
# =========================
@dp.callback_query(F.data == "top")
async def top(call: types.CallbackQuery):
    if not is_admin_full(call.from_user.id):
        return

    top_users = get_top()

    text = "🏆 ТОП:\n\n"
    for i, u in enumerate(top_users, 1):
        text += f"{i}. @{u[0]} — {u[1]}\n"

    await call.message.edit_text(text, reply_markup=admin_kb())


# =========================
# 📊 STATS
# =========================
@dp.callback_query(F.data == "stats")
async def stats(call: types.CallbackQuery):
    users = cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    votes = cursor.execute("SELECT COUNT(*) FROM votes").fetchone()[0]
    battles = cursor.execute("SELECT COUNT(*) FROM battles").fetchone()[0]

    await call.message.edit_text(
        f"📊\n👥 {users}\n🗳 {votes}\n⚔️ {battles}",
        reply_markup=admin_kb()
    )


# =========================
# ⚔️ BATTLES
# =========================
@dp.callback_query(F.data == "battles")
async def battles(call: types.CallbackQuery):
    await call.message.edit_text(
        "⚔️ Управление",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🗑 Очистить голоса", callback_data="clear_votes")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back")]
        ])
    )


@dp.callback_query(F.data == "clear_votes")
async def clear_votes(call: types.CallbackQuery):
    cursor.execute("DELETE FROM votes")
    conn.commit()

    await call.answer("Очищено")
    await call.message.edit_text("✅ Голоса очищены", reply_markup=admin_kb())


# =========================
# ➕ ADD ADMIN
# =========================
@dp.callback_query(F.data == "add_admin")
async def add_admin_btn(call: types.CallbackQuery):
    admin_sessions[call.from_user.id] = "add_admin"
    await call.message.edit_text("Введите ID:")


# =========================
# 🔙 BACK / 🚪 LOGOUT
# =========================
@dp.callback_query(F.data == "back")
async def back(call: types.CallbackQuery):
    await call.message.edit_text("👑 Панель", reply_markup=admin_kb())


@dp.callback_query(F.data == "logout")
async def logout(call: types.CallbackQuery):
    admin_sessions.pop(call.from_user.id, None)
    await call.message.edit_text("🚪 Выход")


# =========================
# 📢 ПРОВЕРКА ПОДПИСКИ
# =========================
@dp.callback_query(F.data == "check_sub")
async def check_subscription(call: types.CallbackQuery):
    if await check_sub(call.from_user.id):
        await call.message.edit_text("✅ Подписка есть")
    else:
        await call.answer("❌ Подпишись", show_alert=True)


# =========================
# 🗳️ ГОЛОСОВАНИЕ
# =========================
@dp.callback_query(F.data.startswith("vote_"))
async def vote(call: types.CallbackQuery):

    user_id = call.from_user.id

    if not await check_sub(user_id):
        await call.answer("❌ Подпишись", show_alert=True)
        return

    _, battle_id, username = call.data.split("_")
    battle_id = int(battle_id)

    if has_voted(battle_id, user_id):
        await call.answer("❌ Уже голосовал")
        return

    add_vote(battle_id, user_id, username)
    await call.answer("✅ Голос принят")


# =========================
# 🚀 ЗАПУСК
# =========================
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
