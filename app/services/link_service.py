from datetime import UTC, datetime
import json

from redis.exceptions import RedisError
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.link import Link
from app.schemas.link import CreateLinkRequest
from app.utils.short_code import generate_base62_code

MAX_CODE_GENERATION_ATTEMPTS = 5
CACHE_TTL = 60 * 60


async def create_link(link_data: CreateLinkRequest, db: AsyncSession):

    original_url = str(link_data.original_url)

    result = await db.execute(
        select(Link).where(Link.original_url == original_url, Link.is_active.is_(True))
    )

    existing_link = result.scalar_one_or_none()

    if existing_link is not None:
        if existing_link.expires_at is None or existing_link.expires_at > datetime.now(UTC):
            return existing_link
        existing_link.is_active = False
        await db.commit()

    for _ in range(MAX_CODE_GENERATION_ATTEMPTS):
        short_code = generate_base62_code()

        link = Link(
            short_code=short_code,
            original_url=original_url,
            expires_at=link_data.expires_at,
            is_active=True,
        )

        db.add(link)

        try:
            await db.commit()
            await db.refresh(link)
            return link
        except IntegrityError:
            await db.rollback()

            result = await db.execute(
                select(Link).where(Link.original_url == original_url, Link.is_active.is_(True))
            )

            existing_link = result.scalar_one_or_none()

            if existing_link is not None:
                return existing_link

    raise RuntimeError("Failed to create a unique short link")


async def resolve_link(short_code: str, db: AsyncSession, redis: Redis):

    cache_key = f"link:{short_code}"

    try:
        cached_link = await redis.get(cache_key)
        if cached_link is not None:
            data = json.loads(cached_link)

            expires_at = (datetime.fromisoformat(data["expires_at"])
                if data["expires_at"] is not None else None)

            is_active = data["is_active"]

            if is_active and (expires_at is None or expires_at > datetime.now(UTC)):
                return {
                    "short_code": short_code,
                    "original_url": data["original_url"],
                    "expires_at": expires_at,
                    "is_active": is_active,
                }

            await redis.delete(cache_key)

    except (RedisError, json.JSONDecodeError, KeyError, ValueError):
        pass

    result = await db.execute(
        select(Link).where(Link.short_code == short_code)
    )

    link = result.scalar_one_or_none()

    if link is None:
        return None

    try:
        cache_data = {
            "original_url": link.original_url,
            "expires_at": (
                link.expires_at.isoformat()
                if link.expires_at is not None
                else None
            ),
            "is_active": link.is_active,
        }

        await redis.set(cache_key, json.dumps(cache_data), ex=CACHE_TTL)

    except RedisError:
        pass

    return link