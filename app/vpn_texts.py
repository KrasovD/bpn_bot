VPN_INSTRUCTIONS = """\
📌 Подключение к VPN (шаблон)

Вариант A — WireGuard:
1) Установи WireGuard:
   • Windows/macOS: официальное приложение WireGuard
   • Linux: sudo apt install wireguard
2) Импортируй конфиг (.conf) в приложение
3) Нажми Activate/Подключить

Вариант B — OpenVPN:
1) Установи OpenVPN Connect
2) Импортируй .ovpn профиль
3) Connect

⚠️ Если скажешь, какой VPN у тебя поднят (WireGuard/OpenVPN/etc) и где лежит конфиг,
я сделаю команду /vpn, которая будет отдавать именно твой файл (как документ) + точные шаги.
"""