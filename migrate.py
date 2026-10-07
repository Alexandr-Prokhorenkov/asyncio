import asyncio

from models import close_db, create_db


async def main():
    await create_db()
    await close_db()


if __name__ == "__main__":
    asyncio.run(main())
