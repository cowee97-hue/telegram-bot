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

# battle_id -> {u1, u2}
battles = {}


# =========================
# CREATE BATTLE
# =========================
def new_battle(u1, u2):
    bid = create_battle(u1, u2)
    battles[bid] = {"u1": u1, "u2": u2}
    return bid


# =========================
# /BATTLE (LIST FOR USERS)
# =========================
@dp.message(F.text == "/battle")
async def battle_list(msg: types.Message):

    if not battles:
        await msg.answer("❌ Нет активных битв")
        return

    kb = []

    for bid, d in battles.items():
        kb.append([
            InlineKeyboardButton(
                text=f"⚔️ @{d['u1']} vs @{d['u2']}",
                callback_data=f"open_{bid}"
            )
        ])

    await msg.answer(
        "🔥 <b>Активные битвы:</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb),
        parse_mode="HTML"
    )


# =========================
# OPEN BATTLE
# =========================
@dp.callback_query(F.data.startswith("open_"))
async def open_battle(call: types.CallbackQuery):

    bid = int(call.data.split("_")[1])

    data = battles.get(bid)

    if not data:
        await call.answer("❌ Битва не найдена")
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔥 @" + data["u1"], callback_data=f"vote_{bid}_1"),
            InlineKeyboardButton(text="⚔️ @" + data["u2"], callback_data=f"vote_{bid}_2")
        ]
    ])

    await call.message.answer(
        f"🔥 @{data['u1']} vs @{data['u2']}",
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

    if not battles:
        await msg.answer("❌ Нет активных битв")
        return

    kb = []

    for bid, d in battles.items():
        kb.append([
            InlineKeyboardButton(
                text=f"🛑 @{d['u1']} vs @{d['u2']}",
                callback_data=f"select_end_{bid}"
            )
        ])

    await msg.answer(
        "👑 <b>Выбери битву:</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb),
        parse_mode="HTML"
    )


# =========================
# SELECT BATTLE TO END
# =========================
@dp.callback_query(F.data.startswith("select_end_"))
async def select_end(call: types.CallbackQuery):

    if call.from_user.id not in admins:
        await call.answer("❌ Нет доступа")
        return

    bid = int(call.data.split("_")[2])

    data = battles.get(bid)

    if not data:
        await call.answer("❌ Битва не найдена")
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🔥 ЗАВЕРШИТЬ",
                callback_data=f"end_{bid}"
            )
        ]
    ])

    await call.message.answer(
        f"⚔️ @{data['u1']} vs @{data['u2']}\n\nПодтверди завершение:",
        reply_markup=kb
    )


# =========================
# END BATTLE
# =========================
@dp.callback_query(F.data.startswith("end_"))
async def end_battle(call: types.CallbackQuery):

    if call.from_user.id not in admins:
        await call.answer("❌ Нет доступа")
        return

    bid = int(call.data.split("_")[1])

    data = battles.get(bid)

    if not data:
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

    u1, u2 = data["u1"], data["u2"]

    if p1 > p2:
        result = f"🏆 Победил @{u1} ({p1}:{p2})"
    elif p2 > p1:
        result = f"🏆 Победил @{u2} ({p2}:{p1})"
    else:
        result = f"🤝 Ничья ({p1}:{p2})"

    await call.message.answer("🛑 Битва завершена\n\n" + result)

    battles.pop(bid, None)

    await call.answer("Готово")


# =========================
# SET ADMIN (OWNER ONLY)
# =========================
@dp.message(F.text.startswith("/setadm"))
async def setadm(msg: types.Message):

    if msg.from_user.id != OWNER_ID:
        await msg.answer("❌ Только Owner может добавлять админов")
        return

    try:
        new_id = int(msg.text.split()[1])
        admins.add(new_id)

        await msg.answer(f"✅ Админ добавлен: {new_id}")
    except:
        await msg.answer("❌ Используй: /setadm ID")


# =========================
# RUN
# =========================
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
