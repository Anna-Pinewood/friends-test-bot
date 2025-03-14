
"""
Entry point for the Friends Test bot.
"""
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from src.handlers import command_handlers, test_creation, test_taking
from src.consts import BOT_TOKEN
from src.db.database import db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] %(name)s: %(message)s',
    datefmt='%H:%M:%S'
)

logger = logging.getLogger(__name__)


async def main():
    """Initialize and start the bot."""
    logger.info("Starting the bot")

    # Initialize database connection
    logger.info("Connecting to database")
    await db.connect()
    logger.info("Database connection established")

    # Initialize bot and dispatcher
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Include routers
    dp.include_router(command_handlers.router)
    dp.include_router(test_creation.router)
    dp.include_router(test_taking.router)

    # Start polling
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Bot started.")

    try:
        await dp.start_polling(bot)
    finally:
        # Close database connection when bot stops
        logger.info("Closing database connection")
        await db.close()


if __name__ == "__main__":
    asyncio.run(main())
