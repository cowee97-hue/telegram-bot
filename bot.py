import asyncio
import os

from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database import create_battle, add_vote, has_voted, cursor

TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = 6287356721

bot = Bot(token=TOKEN)
dp = Dispatcher()

admins = {OWNER_ID}

queue = []

battles = {}  # {id: {"u1": "", "u2": ""}}


# =========================
# CREATE BATTLE
# =========================
def new_battle(u1, u2):
    bid = create_battle(u1, u2)
    battles[bid] = {"u1": u1, "u2": u2}
    return bid


# =========================
# START
# =========================
@dp.message(F.text == "/start")
async def start(msg: types.Message):

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧑‍🤝‍🧑 Участвовать", callback_data="join_queue")],
        [InlineKeyboardButton(text="🗳 Голосовать", callback_data="vote_menu")]
    ])

    await msg.answer("👋 Выбери действие:", reply_markup=kb)


# =========================
# JOIN QUEUE
# =========================
@dp.callback_query(F.data == "join_queue")
async def join_queue(call: types.CallbackQuery):

    user = call.from_user.username

    if not user:
        await call.answer("❌ У вас нет юзернейма", show_alert=True)
        return

    if user in queue:
        await call.answer("⏳ Уже в очереди")
        return

    queue.append(user)

    await call.message.answer(f"✅ @{user} добавлен в очередь")


# =========================
# VOTE MENU (LIST BATTLES)
# =========================
@dp.callback_query(F.data == "vote_menu")
async def vote_menu(call: types.CallbackQuery):

    if not battles:
        await call.message.answer("❌ Нет активных битв")
        return

    kb = []

    for bid, d in battles.items():
        kb.append([
            InlineKeyboardButton(
                text=f"⚔️ @{d['u1']} vs @{d['u2']}",
                callback_data=f"vote_open_{bid}"
            )
        ])

    await call.message.answer(
        "🗳 Выбери битву:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
    )


# =========================
# OPEN VOTE BATTLE
# =========================
@dp.callback_query(F.data.startswith("vote_open_"))
async def vote_open(call: types.CallbackQuery):

    bid = int(call.data.split("_")[2])

    d = battles.get(bid)

    if not d:
        await call.answer("❌ Битва не найдена")
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=f"🔥 @{d['u1']}", callback_data=f"vote_{bid}_1"),
            InlineKeyboardButton(text=f"⚔️ @{d['u2']}", callback_data=f"vote_{bid}_2")
        ]
    ])

    await call.message.answer(
        f"⚔️ @{d['u1']} vs @{d['u2']}\nВыбери голос:",
        reply_markup=kb
    )


# =========================
# VOTE
# =========================
@dp.callback_query(F.data.startswith("vote_"))
async def vote(call: types.CallbackQuery):

    _, bid, opt = call.data.split("_")
    bid = int(bid)

    if has_voted(bid, call.from_user.id):
        await call.answer("❌ Уже голосовал")
        return

    add_vote(bid, call.from_user.id, opt)

    await call.answer("✅ Голос принят")


# =========================
# ADMIN PANEL
# =========================
@dp.message(F.text == "/admin")
async def admin(msg: types.Message):

    if msg.from_user.id not in admins:
        await msg.answer("❌ Нет доступа")
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Список битв", callback_data="list_battles")],
        [InlineKeyboardButton(text="🛑 Завершить битву", callback_data="end_menu")],
        [InlineKeyboardButton(text="👥 Пользователи", callback_data="users_list")],
        [InlineKeyboardButton(text="🏆 Топ пользователей", callback_data="top_users")],
        [InlineKeyboardButton(text="🧹 Удалить голоса", callback_data="delete_votes_menu")]
    ])

    await msg.answer("👑 <b>Админ панель</b>", reply_markup=kb, parse_mode="HTML")


# =========================
# LIST BATTLES
# =========================
@dp.callback_query(F.data == "list_battles")
async def list_battles(call: types.CallbackQuery):

    if not battles:
        await call.message.answer("❌ Нет битв")
        return

    kb = []

    for bid, d in battles.items():
        kb.append([
            InlineKeyboardButton(
                text=f"⚔️ @{d['u1']} vs @{d['u2']}",
                callback_data=f"vote_open_{bid}"
            )
        ])

    await call.message.answer(
        "📋 Битвы:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
    )


# =========================
# END MENU
# =========================
@dp.callback_query(F.data == "end_menu")
async def end_menu(call: types.CallbackQuery):

    if not battles:
        await call.message.answer("❌ Нет битв")
        return

    kb = []

    for bid, d in battles.items():
        kb.append([
            InlineKeyboardButton(
                text=f"🛑 @{d['u1']} vs @{d['u2']}",
                callback_data=f"select_end_{bid}"
            )
        ])

    await call.message.answer(
        "🛑 Выбери битву:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
    )


# =========================
# SELECT END
# =========================
@dp.callback_query(F.data.startswith("select_end_"))
async def select_end(call: types.CallbackQuery):

    bid = int(call.data.split("_")[2])

    d = battles.get(bid)

    if not d:
        await call.answer("❌ Нет битвы")
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔥 ЗАВЕРШИТЬ", callback_data=f"end_{bid}")]
    ])

    await call.message.answer(
        f"⚔️ @{d['u1']} vs @{d['u2']}",
        reply_markup=kb
    )


# =========================
# END BATTLE
# =========================
@dp.callback_query(F.data.startswith("end_"))
async def end_battle(call: types.CallbackQuery):

    bid = int(call.data.split("_")[1])

    d = battles.get(bid)

    if not d:
        await call.answer("❌ Уже завершена")
        return

    stats = cursor.execute(
        "SELECT vote FROM votes WHERE battle_id = ?",
        (bid,)
    ).fetchall()

    p1 = 0
    p2 = 0

    for v in stats:
        if str(v[0]).startswith("1"):
            p1 += 1
        else:
            p2 += 1

    u1, u2 = d["u1"], d["u2"]

    if p1 > p2:
        result = f"🏆 @{u1} ({p1}:{p2})"
    elif p2 > p1:
        result = f"🏆 @{u2} ({p2}:{p1})"
    else:
        result = f"🤝 Ничья ({p1}:{p2})"

    await call.message.answer("🛑 Битва завершена\n\n" + result)

    battles.pop(bid, None)

    await call.answer("Готово")


# =========================
# USERS LIST
# =========================
@dp.callback_query(F.data == "users_list")
async def users_list(call: types.CallbackQuery):

    rows = cursor.execute("SELECT DISTINCT user_id FROM votes").fetchall()

    text = "👥 Пользователи:\n\n"

    for r in rows:
        text += f"{r[0]}\n"

    await call.message.answer(text)


# =========================
# TOP USERS
# =========================
@dp.callback_query(F.data == "top_users")
async def top_users(call: types.CallbackQuery):

    rows = cursor.execute("""
        SELECT user_id, COUNT(*) as c
        FROM votes
        GROUP BY user_id
        ORDER BY c DESC
        LIMIT 10
    """).fetchall()

    text = "🏆 ТОП:\n\n"

    for i, r in enumerate(rows, 1):
        text += f"{i}. {r[0]} — {r[1]}\n"

    await call.message.answer(text)


# =========================
# SET ADMIN
# =========================
@dp.message(F.text.startswith("/setadm"))
async def setadm(msg: types.Message):

    if msg.from_user.id != OWNER_ID:
        await msg.answer("❌ Только Owner")
        return

    try:
        new_id = int(msg.text.split()[1])
        admins.add(new_id)
        await msg.answer(f"✅ Админ: {new_id}")
    except:
        await msg.answer("❌ /setadm ID")


# =========================
# RUN
# =========================
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
