"""Pydantic schemas for diagrams, validation, evaluation, and audit logs."""
import datetime as dt
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


DiagramType = Literal[
    "architecture_azure",
    "architecture_aws",
    "treemap",
    "sankey",
    "slopegraph",
    "dumbbell",
    "waffle",
    "beeswarm",
    "sbgn_pd",
    "rag_pipeline",
]

DiagramTheme = Literal[
    "editorial_light",
    "editorial_dark",
    "blueprint",
    "warm_paper",
]


class DiagramContent(BaseModel):
    eyebrow: Optional[str] = None
    title: str = "Untitled Diagram"
    subtitle: Optional[str] = None
    footnote: Optional[str] = None
    source: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)
    options: Dict[str, Any] = Field(default_factory=dict)


class DiagramCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    diagram_type: DiagramType
    theme: DiagramTheme = "editorial_light"
    content: DiagramContent


class DiagramUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=120)
    diagram_type: Optional[DiagramType] = None
    theme: Optional[DiagramTheme] = None
    content: Optional[DiagramContent] = None


class DiagramResponse(BaseModel):
    id: str
    name: str
    diagram_type: DiagramType
    theme: DiagramTheme
    content: Dict[str, Any]
    created_at: dt.datetime
    updated_at: dt.datetime
    created_by: str

    model_config = ConfigDict(from_attributes=True)


class DiagramListResponse(BaseModel):
    items: List[DiagramResponse]
    total: int
    page: int
    page_size: int


class ValidationIssue(BaseModel):
    rule: str
    severity: Literal["error", "warning", "info"]
    message: str
    element_id: Optional[str] = None


class ValidationReport(BaseModel):
    valid: bool
    diagram_type: DiagramType
    total_checks: int
    issues: List[ValidationIssue]
    passed_rules: List[str]
    honest_data_compliant: bool
    containment_compliant: bool
    skin_compliant: bool


class RenderRequest(BaseModel):
    diagram_type: DiagramType
    theme: DiagramTheme = "editorial_light"
    content: DiagramContent
    format: Literal["svg", "html"] = "svg"


class RenderResponse(BaseModel):
    diagram_type: DiagramType
    theme: DiagramTheme
    svg: str
    html: str
    element_count: int
    render_time_ms: float


class BenchmarkCase(BaseModel):
    id: str
    name: str
    category: str
    diagram_type: DiagramType
    prompt: str
    spec: Dict[str, Any]
    expected_rules: List[str]


class BenchmarkRunItemResult(BaseModel):
    case_id: str
    name: str
    diagram_type: DiagramType
    passed: bool
    validation: ValidationReport
    render_time_ms: float
    error: Optional[str] = None


class EvaluationSummaryResponse(BaseModel):
    run_id: str
    timestamp: dt.datetime
    total_cases: int
    passed_cases: int
    accuracy_rate: float
    containment_compliance_rate: float
    honest_data_rate: float
    avg_render_latency_ms: float
    cases: List[BenchmarkRunItemResult]


class AuditLogEntry(BaseModel):
    id: int
    timestamp: dt.datetime
    user_id: str
    action: str
    resource_type: str
    resource_id: str
    details: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)


class AuditLogResponse(BaseModel):
    items: List[AuditLogEntry]
    total: int
    page: int
    page_size: int


class LLMExplainRequest(BaseModel):
    diagram_id: Optional[str] = None
    spec: Optional[DiagramContent] = None
    question: Optional[str] = None


class LLMExplainResponse(BaseModel):
    provider: str
    model: str
    explanation: str
    grounded_entities: List[str]
    is_advisory: bool = True
    disclaimer: str = "This explanation is an advisory summary grounded in the supplied diagram specification."
