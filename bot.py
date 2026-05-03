import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import F

TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = "@mativstydio"

bot = Bot(token=TOKEN)
dp = Dispatcher()

queue = []
votes = {}
voted_users = set()


# Проверка подписки
async def check_sub(user_id: int):
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status != "left"
    except:
        return False


# /start
@dp.message(F.text == "/start")
async def start(msg: types.Message):
    if not await check_sub(msg.from_user.id):
        await msg.answer("Подпишись на канал: https://t.me/mativstydio")
        return

    username = msg.from_user.username
    if not username:
        await msg.answer("У тебя нет юзернейма!")
        return

    if username in queue:
        await msg.answer("Ты уже в очереди!")
        return

    queue.append(username)
    await msg.answer(f"@{username} добавлен в очередь!")

    if len(queue) == 2:
        user1, user2 = queue[0], queue[1]
        votes[user1] = 0
        votes[user2] = 0

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text=f"@{user1} (0)", callback_data=f"vote_{user1}"),
                InlineKeyboardButton(text=f"@{user2} (0)", callback_data=f"vote_{user2}")
            ]
        ])

        await msg.answer(f"🔥 БИТВА!\n@{user1} VS @{user2}", reply_markup=kb)

        queue.clear()
        voted_users.clear()


# голосование
@dp.callback_query(F.data.startswith("vote_"))
async def vote(call: types.CallbackQuery):
    user_id = call.from_user.id

    if not await check_sub(user_id):
        await call.answer("Подпишись на канал!", show_alert=True)
        return

    if user_id in voted_users:
        await call.answer("Ты уже голосовал!")
        return

    voted_users.add(user_id)

    user = call.data.split("_")[1]
    votes[user] += 1

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=f"@{u} ({votes[u]})", callback_data=f"vote_{u}")
            for u in votes
        ]
    ])

    await call.message.edit_reply_markup(reply_markup=kb)
    await call.answer("Голос засчитан!")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())