import asyncio
import os

from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database import (
    create_battle,
    add_vote,
    has_voted,
    cursor,
    add_admin,
    remove_admin,
    get_admins
)

# =========================
# CONFIG
# =========================
TOKEN = os.getenv("BOT_TOKEN")

OWNER_ID = 7840407227
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
def is_admin(user_id):
    return user_id in admins or user_id == OWNER_ID


async def check_sub(user_id: int):
    try:
        member = await bot.get_chat_member(CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False


def sub_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📢 Подписаться",
                    url="https://t.me/mativstydio"
                )
            ],
            [
                InlineKeyboardButton(
                    text="✅ Я подписался",
                    callback_data="check_sub"
                )
            ]
        ]
    )


def get_votes(battle_id):
    rows = cursor.execute(
        "SELECT vote FROM votes WHERE battle_id = ?",
        (battle_id,)
    ).fetchall()

    p1 = sum(1 for r in rows if str(r[0]) == "1")
    p2 = sum(1 for r in rows if str(r[0]) == "2")

    return p1, p2


def create_new_battle(u1, u2):
    battle_id = create_battle(u1, u2)

    battles[battle_id] = {
        "u1": u1,
        "u2": u2
    }

    return battle_id


# =========================
# START
# =========================
@dp.message(F.text == "/start")
async def start(msg: types.Message):

    if not await check_sub(msg.from_user.id):
        await msg.answer(
            "❗ Подпишись на канал",
            reply_markup=sub_keyboard()
        )
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🧑‍🤝‍🧑 Участвовать",
                    callback_data="join_queue"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🗳 Голосовать",
                    callback_data="vote_menu"
                )
            ]
        ]
    )

    await msg.answer(
        "👋 Добро пожаловать!",
        reply_markup=kb
    )


# =========================
# CHECK SUB
# =========================
@dp.callback_query(F.data == "check_sub")
async def check_subscription(call: types.CallbackQuery):

    if await check_sub(call.from_user.id):
        await call.message.edit_text("✅ Подписка подтверждена")
    else:
        await call.answer(
            "❌ Ты не подписался",
            show_alert=True
        )


# =========================
# JOIN QUEUE
# =========================
@dp.callback_query(F.data == "join_queue")
async def join_queue(call: types.CallbackQuery):

    username = call.from_user.username

    if not username:
        await call.answer(
            "❌ У вас нет username",
            show_alert=True
        )
        return

    if username in queue:
        await call.answer(
            "⏳ Ты уже в очереди"
        )
        return

    queue.append(username)

    await call.message.answer(
        f"✅ @{username} добавлен в очередь"
    )

    if len(queue) >= 2:

        u1 = queue.pop(0)
        u2 = queue.pop(0)

        battle_id = create_new_battle(u1, u2)

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=f"🔥 @{u1} (0)",
                        callback_data=f"vote_{battle_id}_1"
                    ),
                    InlineKeyboardButton(
                        text=f"⚔️ @{u2} (0)",
                        callback_data=f"vote_{battle_id}_2"
                    )
                ]
            ]
        )

        text = f"🔥 БИТВА!\n\n@{u1} ⚔️ @{u2}"

        await call.message.answer(
            text,
            reply_markup=kb
        )

        await bot.send_message(
            CHANNEL,
            text,
            reply_markup=kb
        )

    await call.answer()


# =========================
# BATTLES LIST
# =========================
@dp.callback_query(F.data == "list_battles")
async def list_battles(call: types.CallbackQuery):

    if not is_admin(call.from_user.id):
        await call.answer(
            "❌ Нет доступа",
            show_alert=True
        )
        return

    if not battles:
        await call.message.answer(
            "❌ Нет активных битв"
        )
        await call.answer()
        return

    kb = []

    for battle_id, data in battles.items():

        kb.append([
            InlineKeyboardButton(
                text=f"⚔️ @{data['u1']} vs @{data['u2']}",
                callback_data=f"open_battle_{battle_id}"
            )
        ])

    await call.message.answer(
        "📋 Активные битвы:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=kb
        )
    )

    await call.answer()


# =========================
# OPEN BATTLE
# =========================
@dp.callback_query(F.data.startswith("open_battle_"))
async def open_battle(call: types.CallbackQuery):

    battle_id = int(call.data.split("_")[2])

    data = battles.get(battle_id)

    if not data:
        await call.answer("❌ Битва не найдена")
        return

    p1, p2 = get_votes(battle_id)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"🔥 @{data['u1']} ({p1})",
                    callback_data=f"vote_{battle_id}_1"
                ),
                InlineKeyboardButton(
                    text=f"⚔️ @{data['u2']} ({p2})",
                    callback_data=f"vote_{battle_id}_2"
                )
            ]
        ]
    )

    await call.message.answer(
        f"⚔️ @{data['u1']} vs @{data['u2']}",
        reply_markup=kb
    )

    await call.answer()


# =========================
# VOTE MENU
# =========================
@dp.callback_query(F.data == "vote_menu")
async def vote_menu(call: types.CallbackQuery):

    if not battles:
        await call.message.answer(
            "❌ Нет активных битв"
        )
        await call.answer()
        return

    kb = []

    for battle_id, data in battles.items():

        kb.append([
            InlineKeyboardButton(
                text=f"⚔️ @{data['u1']} vs @{data['u2']}",
                callback_data=f"open_battle_{battle_id}"
            )
        ])

    await call.message.answer(
        "🗳 Выбери битву:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=kb
        )
    )

    await call.answer()


# =========================
# VOTE
# =========================
@dp.callback_query(F.data.startswith("vote_"))
async def vote(call: types.CallbackQuery):

    if not await check_sub(call.from_user.id):
        await call.answer(
            "❌ Подпишись на канал",
            show_alert=True
        )
        return

    _, battle_id, option = call.data.split("_")

    battle_id = int(battle_id)

    if has_voted(battle_id, call.from_user.id):
        await call.answer(
            "❌ Ты уже голосовал"
        )
        return

    add_vote(
        battle_id,
        call.from_user.id,
        option
    )

    data = battles.get(battle_id)

    p1, p2 = get_votes(battle_id)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"🔥 @{data['u1']} ({p1})",
                    callback_data=f"vote_{battle_id}_1"
                ),
                InlineKeyboardButton(
                    text=f"⚔️ @{data['u2']} ({p2})",
                    callback_data=f"vote_{battle_id}_2"
                )
            ]
        ]
    )

    await call.message.edit_reply_markup(
        reply_markup=kb
    )

    await call.answer(
        "✅ Голос принят"
    )


# =========================
# ADMIN PANEL
# =========================
@dp.message(F.text == "/admin")
async def admin_panel(msg: types.Message):

    if not is_admin(msg.from_user.id):
        await msg.answer("❌ Нет доступа")
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📋 Битвы",
                    callback_data="list_battles"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🛑 Завершить",
                    callback_data="end_menu"
                )
            ],
            [
                InlineKeyboardButton(
                    text="👥 Пользователи",
                    callback_data="users_list"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏆 ТОП",
                    callback_data="top_users"
                )
            ]
        ]
    )

    await msg.answer(
        "👑 Админ панель",
        reply_markup=kb
    )


# =========================
# USERS LIST
# =========================
@dp.callback_query(F.data == "users_list")
async def users_list(call: types.CallbackQuery):

    rows = cursor.execute(
        "SELECT DISTINCT user_id FROM votes"
    ).fetchall()

    if not rows:
        await call.message.answer("❌ Нет пользователей")
        await call.answer()
        return

    text = "👥 Пользователи:\n\n"

    for row in rows:

        uid = row[0]

        try:
            user = await bot.get_chat(uid)

            if user.username:
                text += f"@{user.username} ({uid})\n"
            else:
                text += f"{user.first_name} ({uid})\n"

        except:
            text += f"{uid}\n"

    await call.message.answer(text)

    await call.answer()


# =========================
# TOP USERS
# =========================
@dp.callback_query(F.data == "top_users")
async def top_users(call: types.CallbackQuery):

    rows = cursor.execute("""
        SELECT vote, COUNT(*) as c
        FROM votes
        GROUP BY vote
        ORDER BY c DESC
        LIMIT 10
    """).fetchall()

    if not rows:
        await call.message.answer("❌ Нет данных")
        await call.answer()
        return

    text = "🏆 ТОП:\n\n"

    for i, row in enumerate(rows, start=1):

        text += f"{i}. Вариант {row[0]} — {row[1]} голосов\n"

    await call.message.answer(text)

    await call.answer()


# =========================
# END MENU
# =========================
@dp.callback_query(F.data == "end_menu")
async def end_menu(call: types.CallbackQuery):

    if not battles:
        await call.message.answer(
            "❌ Нет активных битв"
        )
        await call.answer()
        return

    kb = []

    for battle_id, data in battles.items():

        kb.append([
            InlineKeyboardButton(
                text=f"🛑 @{data['u1']} vs @{data['u2']}",
                callback_data=f"end_{battle_id}"
            )
        ])

    await call.message.answer(
        "🛑 Выбери битву:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=kb
        )
    )

    await call.answer()


# =========================
# END BATTLE
# =========================
@dp.callback_query(F.data.startswith("end_"))
async def end_battle(call: types.CallbackQuery):

    try:
        battle_id = int(call.data.split("_")[1])
    except:
        await call.answer("❌ Ошибка")
        return

    data = battles.get(battle_id)

    if not data:
        await call.answer("❌ Битва не найдена")
        return

    p1, p2 = get_votes(battle_id)

    u1 = data["u1"]
    u2 = data["u2"]

    if p1 > p2:
        result = f"🏆 @{u1} победил ({p1}:{p2})"
    elif p2 > p1:
        result = f"🏆 @{u2} победил ({p2}:{p1})"
    else:
        result = f"🤝 Ничья ({p1}:{p2})"

    await call.message.answer(
        "🛑 Битва завершена\n\n" + result
    )

    await bot.send_message(
        CHANNEL,
        f"🏆 Результат битвы:\n\n{result}"
    )

    battles.pop(battle_id, None)

    await call.answer(
        "✅ Битва завершена"
    )


# =========================
# ADMIN COMMANDS
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

        await msg.answer(
            f"✅ Админ добавлен: {uid}"
        )

    except:
        await msg.answer(
            "❌ Используй: /setadm ID"
        )


@dp.message(F.text.startswith("/deladm"))
async def deladm(msg: types.Message):

    if msg.from_user.id != OWNER_ID:
        await msg.answer("❌ Только Owner")
        return

    try:
        uid = int(msg.text.split()[1])

        remove_admin(uid)
        admins.discard(uid)

        await msg.answer(
            f"🗑 Админ удалён: {uid}"
        )

    except:
        await msg.answer(
            "❌ Используй: /deladm ID"
        )


@dp.message(F.text == "/admins")
async def admins_list(msg: types.Message):

    data = get_admins()

    if not data:
        await msg.answer("❌ Нет админов")
        return

    text = "👑 Админы:\n\n"

    for uid in data:

        try:
            user = await bot.get_chat(uid)

            if user.username:
                text += f"@{user.username} ({uid})\n"
            else:
                text += f"{user.first_name} ({uid})\n"

        except:
            text += f"{uid}\n"

    await msg.answer(text)


# =========================
# RUN
# =========================
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
