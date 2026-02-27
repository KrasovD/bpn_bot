import asyncio
import time
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from app.config import settings
from app.serverspace_api import ServerspaceAPI
from app.vpn_texts import VPN_INSTRUCTIONS
from app.db import init_db, add_user, get_user, list_users, remove_user, create_invite, use_invite
from app.filters import AuthorizedOnly, AdminOnly
from app.invites import make_token, expires_in_hours

api = ServerspaceAPI(
    base_url=settings.SERVSPACE_API_BASE,
    api_key=settings.SERVSPACE_API_KEY,
)

dp = Dispatcher()

def is_admin(message: Message) -> bool:
    return message.chat.id == settings.ADMIN_CHAT_ID

def admin_only(handler):
    async def wrapper(message: Message, *args, **kwargs):
        if not is_admin(message):
            return await message.answer("⛔️ Доступ только для администратора.")
        return await handler(message, *args, **kwargs)
    return wrapper

@dp.message(Command("start"))
async def start(message: Message):
    u = get_user(message.chat.id)
    if not u:
        return await message.answer(
            "Привет! Доступ закрыт.\n"
            "Если у тебя есть приглашение — введи:\n"
            "/accept <token>"
        )
    await message.answer(
        "Привет! Ты авторизован ✅\n\n"
        "Команды:\n"
        "/balance — баланс\n"
        "/servers — сервера\n"
        "/server <id> — сервер\n"
        "/vpn — VPN инструкция\n\n"
        "Админ:\n"
        "/invite — приглашение\n"
        "/users — список\n"
        "/kick <chat_id> — удалить\n"
    )


@dp.message(Command("balance"))
@admin_only
async def balance(message: Message, *args, **kwargs):
    data = await api.get_project()
    project = data.get("project", {})
    bal = project.get("balance")
    cur = project.get("currency")
    state = project.get("state")
    await message.answer(f"💳 Баланс: {bal} {cur}\nСтатус проекта: {state}")

@dp.message(Command("servers"))
@admin_only
async def servers(message: Message, *args, **kwargs):
    data = await api.list_servers()
    servers_list = data.get("servers", [])
    if not servers_list:
        return await message.answer("Серверов не найдено.")

    lines = []
    for s in servers_list:
        sid = s.get("id")
        name = s.get("name")
        loc = s.get("location_id")
        power = "ON" if s.get("is_power_on") else "OFF"
        ip = None
        nics = s.get("nics") or []
        for nic in nics:
            if nic.get("network_type", "").lower().startswith("public"):
                ip = nic.get("ip_address")
                break
        lines.append(f"• {name} (`{sid}`) [{loc}] {power} IP: {ip or '—'}")

    await message.answer("🖥 Сервера:\n" + "\n".join(lines), parse_mode="Markdown")

@dp.message(Command("server"))
@admin_only
async def server_details(message: Message, command: CommandObject, *args, **kwargs):
    if not command.args:
        return await message.answer("Использование: /server <server_id>")

    server_id = command.args.strip()
    data = await api.get_server(server_id)
    s = data.get("server", {})
    if not s:
        return await message.answer("Не удалось получить сервер (проверь ID).")

    nics = s.get("nics") or []
    public_ips = [nic.get("ip_address") for nic in nics if (nic.get("network_type") or "").lower().startswith("public")]

    text = (
        f"🧩 Сервер: {s.get('name')}\n"
        f"ID: {s.get('id')}\n"
        f"Локация: {s.get('location_id')}\n"
        f"CPU: {s.get('cpu')} | RAM: {s.get('ram_mb')} MB\n"
        f"Power: {'ON' if s.get('is_power_on') else 'OFF'}\n"
        f"State: {s.get('state')}\n"
        f"Public IP: {', '.join([ip for ip in public_ips if ip]) or '—'}\n"
        f"Image: {s.get('image_id')}\n"
    )
    await message.answer(text)

@dp.message(Command("vpn"))
@admin_only
async def vpn(message: Message, *args, **kwargs):
    await message.answer(VPN_INSTRUCTIONS)

async def balance_watcher(bot: Bot):
    """
    Периодически проверяет баланс проекта и шлёт алерт админу,
    когда баланс ниже порога. Чтобы не спамить — троттлим повтор.
    """
    last_alert_ts: float = 0.0
    repeat_cooldown = 60 * 60  # 1 час

    while True:
        try:
            data = await api.get_project()
            project = data.get("project", {})
            bal = float(project.get("balance", 0))
            cur = project.get("currency", "")
            thr = float(settings.LOW_BALANCE_THRESHOLD)

            now = time.time()
            if bal < thr and (now - last_alert_ts) > repeat_cooldown:
                await bot.send_message(
                    settings.ADMIN_CHAT_ID,
                    f"🚨 Низкий баланс Serverspace: {bal} {cur} (порог {thr} {cur})"
                )
                last_alert_ts = now

        except Exception as e:
            pass

        await asyncio.sleep(settings.BALANCE_CHECK_EVERY_SECONDS)


@dp.message(Command("accept"))
async def accept_invite(message: Message, command: CommandObject):
    if not command.args:
        return await message.answer("Использование: /accept <token>")

    token = command.args.strip()
    now = int(time.time())
    invite = use_invite(token, used_by=message.chat.id, now_ts=now)
    if not invite:
        return await message.answer("❌ Инвайт недействителен, истёк или уже использован.")

    add_user(message.chat.id, invite["role"])
    await message.answer(f"✅ Готово! Тебе выдан доступ с ролью: {invite['role']}")

@dp.message(AdminOnly(), Command("invite"))
async def invite(message: Message, command: CommandObject):
    # /invite [hours] [role]
    # примеры: /invite, /invite 24, /invite 24 user, /invite 2 admin
    hours = 24
    role = "user"

    if command.args:
        parts = command.args.split()
        if len(parts) >= 1 and parts[0].isdigit():
            hours = max(1, min(168, int(parts[0])))  # 1..168 часов
        if len(parts) >= 2 and parts[1] in ("user", "admin"):
            role = parts[1]

    token = make_token()
    exp = expires_in_hours(hours)
    create_invite(token=token, created_by=message.chat.id, role=role, expires_at=exp)

    await message.answer(
        f"🎟 Инвайт создан\n"
        f"Роль: {role}\n"
        f"Живёт: {hours}ч\n\n"
        f"Пусть человек напишет боту:\n"
        f"/accept {token}"
    )

@dp.message(AdminOnly(), Command("users"))
async def users_cmd(message: Message):
    users = list_users()
    if not users:
        return await message.answer("Пользователей нет.")
    lines = [f"• {u['chat_id']} — {u['role']} — {u['added_at']}" for u in users]
    await message.answer("👥 Пользователи:\n" + "\n".join(lines))

@dp.message(AdminOnly(), Command("kick"))
async def kick_cmd(message: Message, command: CommandObject):
    if not command.args or not command.args.strip().isdigit():
        return await message.answer("Использование: /kick <chat_id>")

    cid = int(command.args.strip())
    if cid == settings.ADMIN_CHAT_ID:
        return await message.answer("Нельзя удалить владельца 🙂")

    remove_user(cid)
    await message.answer(f"✅ Пользователь {cid} удалён.")

# --- Пример: закрываем команды только для авторизованных:
@dp.message(AuthorizedOnly(), Command("vpn"))
async def vpn(message: Message):
    # твой VPN_INSTRUCTIONS
    await message.answer("...")


async def main():
    init_db()
    bot = Bot(token=settings.BOT_TOKEN)
    add_user(settings.ADMIN_CHAT_ID, "admin")

    asyncio.create_task(balance_watcher(bot))
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())