import asyncio
import logging
import os
from aiohttp import web

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from database.engine import engine, init_db
from config import BOT_TOKEN
from middlewares.auth import AuthMiddleware

from handlers import start, menu, buy, test_account, my_services, wallet, referral, support
from handlers.admin import dashboard, orders, products, users, discounts, settings, admins, card


# ─── Simple HTTP server for Railway health check ──────────────
async def handle_health(request):
    return web.Response(text="OK", status=200)


async def start_http_server():
    app = web.Application()
    app.router.add_get("/", handle_health)
    app.router.add_get("/health", handle_health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()
    logging.info("🌐 HTTP server started on port 8080")


# ─── Main ─────────────────────────────────────────────────────
async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # ساخت پوشه data اگر وجود نداشت
    os.makedirs("data", exist_ok=True)

    # ساخت جداول دیتابیس
    await init_db()

    # Start HTTP server (for Railway)
    await start_http_server()

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    # Register middleware
    dp.message.middleware(AuthMiddleware())
    dp.callback_query.middleware(AuthMiddleware())

    # Register user routers
    dp.include_routers(
        start.router,
        menu.router,
        buy.router,
        test_account.router,
        my_services.router,
        wallet.router,
        referral.router,
        support.router,
    )

    # Register admin routers
    dp.include_routers(
        dashboard.router,
        orders.router,
        products.router,
        users.router,
        discounts.router,
        settings.router,
        admins.router,
        card.router,
    )

    logging.info("🤖 Bot starting...")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
