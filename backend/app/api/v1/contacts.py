from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.contact import Contact, ContactEmail, ContactPhone
from app.models.workspace import User
from app.schemas.contact import ContactCreate, ContactOut, ContactUpdate

router = APIRouter(prefix="/workspaces/{workspace_id}/contacts", tags=["contacts"])


@router.post("", response_model=ContactOut, status_code=201)
async def create_contact(
    workspace_id: UUID,
    body: ContactCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    contact = Contact(
        workspace_id=workspace_id,
        name=body.name,
        type=body.type,
        document=body.document,
        company=body.company,
        integration_id=body.integration_id,
    )
    db.add(contact)
    await db.flush()
    for p in body.phones:
        db.add(ContactPhone(contact_id=contact.id, workspace_id=workspace_id, **p.model_dump()))
    for e in body.emails:
        db.add(ContactEmail(contact_id=contact.id, workspace_id=workspace_id, **e.model_dump()))
    return contact


@router.get("", response_model=dict)
async def list_contacts(
    workspace_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
):
    q = select(Contact).where(Contact.workspace_id == workspace_id)
    if search:
        q = q.where(Contact.name.ilike(f"%{search}%"))
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    q = q.order_by(Contact.name).offset((page - 1) * page_size).limit(page_size)
    items = (await db.execute(q)).scalars().all()
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/{contact_id}", response_model=ContactOut)
async def get_contact(
    workspace_id: UUID,
    contact_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    contact = await db.get(Contact, contact_id)
    if not contact or contact.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


@router.patch("/{contact_id}", response_model=ContactOut)
async def update_contact(
    workspace_id: UUID,
    contact_id: UUID,
    body: ContactUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    contact = await db.get(Contact, contact_id)
    if not contact or contact.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Contact not found")
    for field, val in body.model_dump(exclude_none=True).items():
        setattr(contact, field, val)
    return contact


@router.delete("/{contact_id}", status_code=204)
async def delete_contact(
    workspace_id: UUID,
    contact_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    contact = await db.get(Contact, contact_id)
    if not contact or contact.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Contact not found")
    await db.delete(contact)
