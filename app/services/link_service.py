from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.link import Link
from app.schemas.link import CreateLinkRequest
from app.utils.short_code import generate_base62_code


MAX_CODE_GENERATION_ATTEMPTS = 5


async def create_link(link_data: CreateLinkRequest, db: AsyncSession):

    for _ in range(MAX_CODE_GENERATION_ATTEMPTS):
        short_code = generate_base62_code()

        link = Link(
            short_code=short_code,
            original_url=str(link_data.original_url),
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

    raise RuntimeError("Failed to generate a unique short code")


async def resolve_link(short_code: str, db: AsyncSession):
    result = await db.execute(
        select(Link).where(Link.short_code == short_code)
    )

    return result.scalar_one_or_none()