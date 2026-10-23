# Администрирование

1. Установите зависимости и настройте .env.
2. При безопасных ADMIN_USERNAME и ADMIN_PASSWORD первый пользователь создаётся при старте. Если в .env оставлены шаблонные значения, используйте python -m app.admin create-user admin и задайте пароль интерактивно. Команда python -m app.admin bootstrap проверяет учётные данные из .env. Для дополнительных пользователей выполните python -m app.admin create-user <username>; пароль вводится интерактивно. Для смены используйте reset-password, list-users показывает учётные записи.
3. Откройте /admin/login. Сессия подписана, ограничена по времени, cookie HttpOnly и SameSite=Strict. HTTPS_ONLY включает Secure cookie.
4. Панель показывает сводную статистику и позволяет загружать, создавать и удалять рекламные баннеры.
5. Настройки языка, интервала баннеров и объявления находятся по ссылке «Настройки сайта».

Ограничение попыток входа и rate limit действуют только внутри процесса. Не создавайте общие учетные записи для нескольких операторов.

Admin read requests are limited to 30/minute and writes to 10/minute per IP. Login attempts are limited to five per IP per 15 minutes. Mutations verify same-origin and a double-submit CSRF token.
