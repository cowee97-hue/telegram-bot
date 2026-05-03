import asyncio
import os

from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database import (
    add_user,
    create_battle,
    add_vote,
    has_voted
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
# 📢 ПОДПИСКА
# =========================
async def check_sub(user_id: int):
    try:
        member = await bot.get_chat_member(CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False


# =========================
# 👑 АДМИН (если дальше пригодится)
# =========================
def is_owner(user_id: int):
    return user_id == OWNER_ID


# =========================
# 🚀 START
# =========================
@dp.message(F.text == "/start")
async def start(msg: types.Message):

    user_id = msg.from_user.id
    username = msg.from_user.username

    # проверка подписки
    if not await check_sub(user_id):
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Подписаться", url="https://t.me/mativstydio")],
            [InlineKeyboardButton(text="✅ Я подписался", callback_data="check_sub")]
        ])

        await msg.answer("❗ Подпишись на канал, чтобы использовать бота:", reply_markup=kb)
        return

    if not username:
        await msg.answer("❌ Нужен username в Telegram")
        return

    # сохраняем пользователя в БД
    add_user(user_id, username)

    if username in queue:
        await msg.answer("⏳ Ты уже в очереди")
        return

    queue.append(username)
    await msg.answer(f"✅ @{username} добавлен в очередь")

    # =========================
    # ⚔️ БИТВА
    # =========================
    if len(queue) >= 2:
        u1 = queue.pop(0)
        u2 = queue.pop(0)

        battle_id = create_battle(u1, u2)

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"🔥 @{u1} (0)",
                    callback_data=f"vote_{battle_id}_{u1}"
                ),
                InlineKeyboardButton(
                    text=f"⚔️ @{u2} (0)",
                    callback_data=f"vote_{battle_id}_{u2}"
                )
            ]
        ])

        await msg.answer(
            f"🔥 БИТВА НАЧАЛАСЬ!\n\n@{u1} ⚔️ @{u2}",
            reply_markup=kb
        )


# =========================
# 📢 ПРОВЕРКА ПОДПИСКИ (кнопка)
# =========================
@dp.callback_query(F.data == "check_sub")
async def check_subscription(call: types.CallbackQuery):

    if await check_sub(call.from_user.id):
        await call.message.edit_text("✅ Подписка подтверждена!")
    else:
        await call.answer("❌ Ты не подписался", show_alert=True)


# =========================
# 🗳️ ГОЛОСОВАНИЕ
# =========================
@dp.callback_query(F.data.startswith("vote_"))
async def vote(call: types.CallbackQuery):

    user_id = call.from_user.id

    if not await check_sub(user_id):
        await call.answer("❌ Сначала подпишись на канал", show_alert=True)
        return

    _, battle_id, username = call.data.split("_")
    battle_id = int(battle_id)

    # защита от повторного голосования
    if has_voted(battle_id, user_id):
        await call.answer("❌ Ты уже голосовал")
        return

    add_vote(battle_id, user_id, username)

    await call.answer("✅ Голос засчитан")


# =========================
# 🚀 ЗАПУСК
# =========================
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
