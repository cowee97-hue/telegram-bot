import asyncio
import os

from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database import (
    create_battle, add_vote, has_voted, cursor,
    add_admin, remove_admin, get_admins
)

TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = 6287356721
CHANNEL = "@mativstydio"

bot = Bot(token=TOKEN)
dp = Dispatcher()

queue = []
battles = {}

admins = set(get_admins())
admins.add(OWNER_ID)


# =========================
# UTILS
# =========================
def is_admin(uid):
    return uid in admins or uid == OWNER_ID


async def check_sub(user_id: int):
    try:
        member = await bot.get_chat_member(CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False


def sub_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Подписаться", url="https://t.me/mativstydio")],
        [InlineKeyboardButton(text="✅ Я подписался", callback_data="check_sub")]
    ])


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

    if not await check_sub(msg.from_user.id):
        await msg.answer("❗ Подпишись на канал", reply_markup=sub_kb())
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧑‍🤝‍🧑 Участвовать", callback_data="join_queue")],
        [InlineKeyboardButton(text="🗳 Голосовать", callback_data="vote_menu")]
    ])

    await msg.answer("👋 Выбери действие:", reply_markup=kb)


# =========================
# CHECK SUB
# =========================
@dp.callback_query(F.data == "check_sub")
async def check_subscription(call: types.CallbackQuery):

    if await check_sub(call.from_user.id):
        await call.message.edit_text("✅ Подписка подтверждена!")
    else:
        await call.answer("❌ Ты не подписался", show_alert=True)


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

    if len(queue) >= 2:
        u1 = queue.pop(0)
        u2 = queue.pop(0)

        bid = new_battle(u1, u2)

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text=f"🔥 @{u1}", callback_data=f"vote_{bid}_1"),
                InlineKeyboardButton(text=f"⚔️ @{u2}", callback_data=f"vote_{bid}_2")
            ]
        ])

        await call.message.answer(f"🔥 БИТВА!\n@{u1} ⚔️ @{u2}", reply_markup=kb)

        await bot.send_message(
            chat_id=CHANNEL,
            text=f"🔥 НОВАЯ БИТВА!\n\n@{u1} ⚔️ @{u2}",
            reply_markup=kb
        )


# =========================
# VOTE MENU
# =========================
@dp.callback_query(F.data == "vote_menu")
async def vote_menu(call: types.CallbackQuery):

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
        "🗳 Выбери битву:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
    )


# =========================
# OPEN BATTLE
# =========================
@dp.callback_query(F.data.startswith("vote_open_"))
async def vote_open(call: types.CallbackQuery):

    bid = int(call.data.split("_")[2])
    d = battles.get(bid)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=f"🔥 @{d['u1']}", callback_data=f"vote_{bid}_1"),
            InlineKeyboardButton(text=f"⚔️ @{d['u2']}", callback_data=f"vote_{bid}_2")
        ]
    ])

    await call.message.answer(
        f"⚔️ @{d['u1']} vs @{d['u2']}",
        reply_markup=kb
    )


# =========================
# VOTE
# =========================
@dp.callback_query(F.data.startswith("vote_"))
async def vote(call: types.CallbackQuery):

    if not await check_sub(call.from_user.id):
        await call.answer("❌ Подпишись", show_alert=True)
        return

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

    if not is_admin(msg.from_user.id):
        await msg.answer("❌ Нет доступа")
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Битвы", callback_data="list_battles")],
        [InlineKeyboardButton(text="🛑 Завершить", callback_data="end_menu")],
        [InlineKeyboardButton(text="👥 Пользователи", callback_data="users_list")],
        [InlineKeyboardButton(text="🏆 ТОП", callback_data="top_users")],
        [InlineKeyboardButton(text="🧹 Удалить голоса", callback_data="delete_votes_menu")]
    ])

    await msg.answer("👑 Админ панель", reply_markup=kb)


# =========================
# SET ADMIN
# =========================
@dp.message(F.text.startswith("/setadm"))
async def setadm(msg: types.Message):

    if msg.from_user.id != OWNER_ID:
        await msg.answer("❌ Только Owner")
        return

    try:
        uid = int(msg.text.split()[1])
        add_admin(uid)
        admins.add(uid)

        await msg.answer(f"✅ Админ добавлен: {uid}")
    except:
        await msg.answer("❌ /setadm ID")


# =========================
# DELETE ADMIN
# =========================
@dp.message(F.text.startswith("/deladm"))
async def deladm(msg: types.Message):

    if msg.from_user.id != OWNER_ID:
        await msg.answer("❌ Только Owner")
        return

    try:
        uid = int(msg.text.split()[1])
        remove_admin(uid)
        admins.discard(uid)

        await msg.answer(f"🗑 Удалён: {uid}")
    except:
        await msg.answer("❌ /deladm ID")


# =========================
# LIST ADMINS
# =========================
@dp.message(F.text == "/admins")
async def admins_list(msg: types.Message):

    if not is_admin(msg.from_user.id):
        await msg.answer("❌ Нет доступа")
        return

    data = get_admins()

    text = "👑 Админы:\n\n"
    for uid in data:
        text += f"{uid}\n"

    await msg.answer(text)


# =========================
# RUN
# =========================
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
