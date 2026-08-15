from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.link import Link
from app.schemas.link import CreateLinkRequest
from app.utils.short_code import generate_base62_code

MAX_CODE_GENERATION_ATTEMPTS = 5


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


async def resolve_link(short_code: str, db: AsyncSession):
    result = await db.execute(
        select(Link).where(Link.short_code == short_code)
    )

    return result.scalar_one_or_none()