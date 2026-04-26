import asyncpg


async def create_pool(
    host: str,
    port: int,
    db: str,
    user: str,
    password: str,
    min_size: int = 2,
    max_size: int = 10,
):
    return await asyncpg.create_pool(
        host=host,
        port=port,
        database=db,
        user=user,
        password=password,
        min_size=min_size,
        max_size=max_size,
    )
