"""AI/ML Coding Agent benchmark evaluation endpoints."""
import json
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import AuthenticatedUser, require_role
from app.models.entities import EvaluationRunEntity
from app.models.schemas import BenchmarkCase, EvaluationSummaryResponse
from app.services.evaluator import BENCHMARK_DATASET, BenchmarkEvaluator

router = APIRouter(prefix="/evaluation", tags=["Evaluation"])


@router.get("/cases", response_model=List[BenchmarkCase])
def list_benchmark_cases(
    user: AuthenticatedUser = Depends(require_role("viewer")),
):
    """Returns the labeled dataset of coding agent benchmark cases."""
    return BENCHMARK_DATASET


@router.post("/run", response_model=EvaluationSummaryResponse)
def run_benchmark_evaluation(
    db: Session = Depends(get_db),
    user: AuthenticatedUser = Depends(require_role("analyst")),
):
    """Executes the full offline evaluation suite, measuring accuracy and containment rates."""
    evaluator = BenchmarkEvaluator()
    summary = evaluator.run_suite(BENCHMARK_DATASET)

    # Persist run record
    run_record = EvaluationRunEntity(
        id=summary.run_id,
        timestamp=summary.timestamp,
        total_cases=summary.total_cases,
        passed_cases=summary.passed_cases,
        accuracy_rate=summary.accuracy_rate,
        details_json=json.dumps(summary.model_dump(), default=str),
    )
    db.add(run_record)
    db.commit()

    return summary


@router.get("/history", response_model=List[dict])
def get_evaluation_history(
    db: Session = Depends(get_db),
    user: AuthenticatedUser = Depends(require_role("viewer")),
):
    """Retrieves recent evaluation runs and accuracy trends."""
    records = db.query(EvaluationRunEntity).order_by(EvaluationRunEntity.timestamp.desc()).limit(10).all()
    return [
        {
            "id": r.id,
            "timestamp": r.timestamp,
            "total_cases": r.total_cases,
            "passed_cases": r.passed_cases,
            "accuracy_rate": r.accuracy_rate,
        }
        for r in records
    ]
