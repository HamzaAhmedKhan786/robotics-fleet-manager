import asyncio

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from apps.backend.db.session import engine


async def main():
    try:
        async with engine.connect() as connection:
            result = await connection.execute(text("SELECT current_database()"))

            print("SQLAlchemy connection successful!")
            print("Database:", result.scalar_one())

    except SQLAlchemyError as exc:
        print("Connection failed:", type(exc).__name__)

    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
