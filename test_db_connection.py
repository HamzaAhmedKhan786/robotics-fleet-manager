
import asyncio
import os

import asyncpg
from dotenv import load_dotenv

load_dotenv()


async def main():
    connection = None

    try:
        connection = await asyncpg.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            database=os.getenv("POSTGRES_DB", "robotics_fleet"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD"),
            timeout=5,
        )

        version = await connection.fetchval("SELECT version()")
        database = await connection.fetchval(
            "SELECT current_database()"
        )

        print("PostgreSQL connection successful!")
        print("Connected database:", database)
        print("Server:", version.split(",")[0])

    except Exception as exc:
        print("Connection failed:", type(exc).__name__)
        print("Check your .env credentials and PostgreSQL service.")

    finally:
        if connection is not None:
            await connection.close()


if __name__ == "__main__":
    asyncio.run(main())
