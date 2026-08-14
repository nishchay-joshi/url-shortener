from datetime import datetime, UTC

from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.schemas.link import CreateLinkRequest, LinkResponse
from app.services.link_service import create_link, resolve_link


router = APIRouter()
redirect_router = APIRouter()


@router.post("/links", response_model=LinkResponse, status_code=status.HTTP_201_CREATED)
async def create_short_link(link_data: CreateLinkRequest, db: AsyncSession = Depends(get_db)):
    link = await create_link(link_data=link_data, db=db)

    short_url = f"{settings.base_url}/{link.short_code}"

    return LinkResponse(
        id=link.id,
        short_code=link.short_code,
        short_url=short_url,
        original_url=link.original_url,
        expires_at=link.expires_at,
        created_at=link.created_at,
        is_active=link.is_active,
    )


@redirect_router.get("/{short_code}")
async def redirect_to_original_url(short_code: str, db: AsyncSession = Depends(get_db)):
    link = await resolve_link(short_code=short_code, db=db)

    if link is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Short link not found",
        )

    if not link.is_active:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Short link is inactive",
        )

    if link.expires_at is not None and link.expires_at <= datetime.now(UTC):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Short link has expired",
        )

    return RedirectResponse(
        url=str(link.original_url),
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    )