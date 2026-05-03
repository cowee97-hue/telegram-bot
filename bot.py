#    import asyncio
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
# ⚙️ CONFIG
# =========================
TOKEN = os.getenv("BOT_TOKEN")

OWNER_ID = 6287356721

bot = Bot(token=TOKEN)
dp = Dispatcher()

queue = []

# 👑 админы (без паролей)
admins = {OWNER_ID}

# =========================
# 📢 CHECK SUB
# =========================
CHANNEL = "@mativstydio"

async def check_sub(user_id: int):
    try:
        member = await bot.get_chat_member(CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False


# =========================
# 👑 ADMIN MENU
# =========================
def admin_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Users", callback_data="adm_users")],
        [InlineKeyboardButton(text="🏆 Top", callback_data="adm_top")],
        [InlineKeyboardButton(text="📊 Stats", callback_data="adm_stats")],
        [InlineKeyboardButton(text="🗑 Clear votes", callback_data="adm_clear")],
        [InlineKeyboardButton(text="➕ Add admin", callback_data="adm_add")]
    ])


# =========================
# 🚀 START
# =========================
@dp.message(F.text == "/start")
async def start(msg: types.Message):

    uid = msg.from_user.id
    username = msg.from_user.username

    if not await check_sub(uid):
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Подписаться", url=f"https://t.me/{CHANNEL.replace('@','')}")],
            [InlineKeyboardButton(text="✅ Проверить", callback_data="check_sub")]
        ])
        await msg.answer("❗ Подпишись:", reply_markup=kb)
        return

    if not username:
        await msg.answer("❌ Нужен username")
        return

    add_user(uid, username)

    if username in queue:
        await msg.answer("⏳ Уже в очереди")
        return

    queue.append(username)
    await msg.answer(f"✅ @{username} в очереди")

    # =========================
    # ⚔️ BATTLE
    # =========================
    if len(queue) >= 2:
        u1 = queue.pop(0)
        u2 = queue.pop(0)

        battle_id = create_battle(u1, u2)

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text=f"🔥 @{u
