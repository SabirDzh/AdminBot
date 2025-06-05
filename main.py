import asyncio
import logging
from aiogram import Bot, Dispatcher
import asyncpg
from aiogram.fsm.storage.memory import MemoryStorage
from AdminBot.config import TOKEN_API
from AdminBot.BotBody import command_router, message_router

bot = Bot(TOKEN_API)
dp = Dispatcher(storage=MemoryStorage())


async def main():
    dp.include_router(command_router)
    dp.include_router(message_router)

    try:
        pool = await asyncpg.create_pool(
            user="postgres",
            password="1111",
            database="postgres",
            host="localhost"
        )
        dp["pool"] = pool
    except asyncpg.PostgresError as e:
        logging.error(f"Ошибка подключения к БД: {e}")
        return

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await pool.close()
        await bot.session.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Exit")

# import asyncio
# import logging
# from app.database.models import init_db
# from aiogram import Bot, Dispatcher
#
# from config import TOKEN_API
# from app.AiTeleBot import router
#
# bot = Bot(TOKEN_API)
# dp = Dispatcher()
#
#
# async def main():
#     await init_db()
#     dp.include_router(router)
#     await bot.delete_webhook()
#     await bot.delete_webhook(drop_pending_updates=True)
#     await dp.start_polling(bot)
#
# if __name__ == "__main__":
#     logging.basicConfig(level=logging.INFO)
#     try:
#         asyncio.run(main())
#     except KeyboardInterrupt:
#         print("Exit")
