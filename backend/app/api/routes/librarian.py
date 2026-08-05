import asyncio
from dataclasses import asdict
from typing import cast

from fastapi import APIRouter, HTTPException, Request

from app.schemas.librarian import (
    LibrarianHealthResponse,
    LibrarianItemResponse,
    LibrarianReviewResponse,
)
from app.services.librarian import LibrarianItemNotFoundError, LibrarianService

router = APIRouter(prefix="/librarian", tags=["librarian"])


@router.get("/health", response_model=LibrarianHealthResponse)
async def librarian_health(request: Request) -> LibrarianHealthResponse:
    report = await asyncio.to_thread(_librarian(request).health)
    return LibrarianHealthResponse(**asdict(report))


@router.get("/review", response_model=LibrarianReviewResponse)
async def librarian_review(request: Request) -> LibrarianReviewResponse:
    report = await asyncio.to_thread(_librarian(request).review)
    return LibrarianReviewResponse(**asdict(report))


@router.get("/item/{item_id}", response_model=LibrarianItemResponse)
async def librarian_item(
    item_id: str,
    request: Request,
) -> LibrarianItemResponse:
    try:
        item = await asyncio.to_thread(_librarian(request).item, item_id)
    except LibrarianItemNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail="Librarian review item not found in the current analysis.",
        ) from error
    return LibrarianItemResponse(**asdict(item))


def _librarian(request: Request) -> LibrarianService:
    return cast(LibrarianService, request.app.state.librarian)
