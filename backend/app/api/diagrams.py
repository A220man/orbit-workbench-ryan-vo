"""Diagram lifecycle, compilation, validation, and rendering endpoints."""
import json
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import AuthenticatedUser, get_current_user, require_role
from app.models.entities import AuditEntity, DiagramEntity
from app.models.schemas import (
    DiagramContent,
    DiagramCreate,
    DiagramListResponse,
    DiagramResponse,
    DiagramUpdate,
    LLMExplainRequest,
    LLMExplainResponse,
    RenderRequest,
    RenderResponse,
    ValidationReport,
)
from app.services.engine import EditorialEngine
from app.services.llm_adapter import LLMAdapter
from app.services.validator import DiagramValidator

router = APIRouter(prefix="/diagrams", tags=["Diagrams"])


def record_audit(
    db: Session,
    user_id: str,
    action: str,
    resource_type: str,
    resource_id: str,
    details: dict,
) -> None:
    entry = AuditEntity(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details_json=json.dumps(details),
    )
    db.add(entry)


@router.post("", response_model=DiagramResponse, status_code=status.HTTP_201_CREATED)
def create_diagram(
    payload: DiagramCreate,
    db: Session = Depends(get_db),
    user: AuthenticatedUser = Depends(require_role("analyst")),
):
    """Creates a new diagram specification with persistent storage and audit trail."""
    new_id = str(uuid.uuid4())
    record = DiagramEntity(
        id=new_id,
        name=payload.name,
        diagram_type=payload.diagram_type,
        theme=payload.theme,
        content_json=json.dumps(payload.content.model_dump()),
        created_by=user.user_id,
    )
    db.add(record)
    record_audit(db, user.user_id, "CREATE_DIAGRAM", "diagram", new_id, {"name": payload.name, "type": payload.diagram_type})
    db.commit()
    db.refresh(record)

    return DiagramResponse(
        id=record.id,
        name=record.name,
        diagram_type=record.diagram_type,  # type: ignore
        theme=record.theme,  # type: ignore
        content=record.content,
        created_at=record.created_at,
        updated_at=record.updated_at,
        created_by=record.created_by,
    )


@router.get("", response_model=DiagramListResponse)
def list_diagrams(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    diagram_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user: AuthenticatedUser = Depends(require_role("viewer")),
):
    """Lists saved diagrams with pagination and type filtering."""
    query = db.query(DiagramEntity)
    if diagram_type:
        query = query.filter(DiagramEntity.diagram_type == diagram_type)
    if search:
        query = query.filter(DiagramEntity.name.ilike(f"%{search}%"))

    total = query.count()
    records = query.order_by(DiagramEntity.updated_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    items = [
        DiagramResponse(
            id=r.id,
            name=r.name,
            diagram_type=r.diagram_type,  # type: ignore
            theme=r.theme,  # type: ignore
            content=r.content,
            created_at=r.created_at,
            updated_at=r.updated_at,
            created_by=r.created_by,
        )
        for r in records
    ]
    return DiagramListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{diagram_id}", response_model=DiagramResponse)
def get_diagram(
    diagram_id: str,
    db: Session = Depends(get_db),
    user: AuthenticatedUser = Depends(require_role("viewer")),
):
    """Retrieves a single diagram specification."""
    record = db.query(DiagramEntity).filter(DiagramEntity.id == diagram_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Diagram not found")

    return DiagramResponse(
        id=record.id,
        name=record.name,
        diagram_type=record.diagram_type,  # type: ignore
        theme=record.theme,  # type: ignore
        content=record.content,
        created_at=record.created_at,
        updated_at=record.updated_at,
        created_by=record.created_by,
    )


@router.put("/{diagram_id}", response_model=DiagramResponse)
def update_diagram(
    diagram_id: str,
    payload: DiagramUpdate,
    db: Session = Depends(get_db),
    user: AuthenticatedUser = Depends(require_role("analyst")),
):
    """Updates an existing diagram."""
    record = db.query(DiagramEntity).filter(DiagramEntity.id == diagram_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Diagram not found")

    if payload.name is not None:
        record.name = payload.name
    if payload.diagram_type is not None:
        record.diagram_type = payload.diagram_type
    if payload.theme is not None:
        record.theme = payload.theme
    if payload.content is not None:
        record.content = payload.content.model_dump()

    record_audit(db, user.user_id, "UPDATE_DIAGRAM", "diagram", diagram_id, {"updated_fields": payload.model_dump(exclude_unset=True)})
    db.commit()
    db.refresh(record)

    return DiagramResponse(
        id=record.id,
        name=record.name,
        diagram_type=record.diagram_type,  # type: ignore
        theme=record.theme,  # type: ignore
        content=record.content,
        created_at=record.created_at,
        updated_at=record.updated_at,
        created_by=record.created_by,
    )


@router.delete("/{diagram_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_diagram(
    diagram_id: str,
    db: Session = Depends(get_db),
    user: AuthenticatedUser = Depends(require_role("admin")),
):
    """Deletes a diagram (admin only)."""
    record = db.query(DiagramEntity).filter(DiagramEntity.id == diagram_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Diagram not found")

    db.delete(record)
    record_audit(db, user.user_id, "DELETE_DIAGRAM", "diagram", diagram_id, {"name": record.name})
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/render", response_model=RenderResponse)
def render_live_diagram(
    payload: RenderRequest,
    user: AuthenticatedUser = Depends(require_role("viewer")),
):
    """Compiles a declarative specification into publication-ready SVG and HTML on the fly."""
    engine = EditorialEngine(theme_name=payload.theme)
    return engine.render(payload.diagram_type, payload.content)


@router.post("/validate", response_model=ValidationReport)
def validate_live_diagram(
    payload: RenderRequest,
    user: AuthenticatedUser = Depends(require_role("viewer")),
):
    """Validates structural containment, PaaS isolation, and honest-data rules."""
    engine = EditorialEngine(theme_name=payload.theme)
    rendered = engine.render(payload.diagram_type, payload.content)
    return DiagramValidator.validate(payload.diagram_type, payload.content, rendered.svg)


@router.post("/explain", response_model=LLMExplainResponse)
async def explain_diagram(
    payload: LLMExplainRequest,
    db: Session = Depends(get_db),
    user: AuthenticatedUser = Depends(require_role("viewer")),
):
    """Generates an opt-in advisory LLM explanation grounded in the diagram record."""
    spec_content = payload.spec
    if not spec_content and payload.diagram_id:
        record = db.query(DiagramEntity).filter(DiagramEntity.id == payload.diagram_id).first()
        if record:
            spec_content = DiagramContent(**record.content)

    if not spec_content:
        raise HTTPException(status_code=400, detail="Either diagram_id or spec must be provided")

    return await LLMAdapter.explain_diagram(spec_content, question=payload.question)
