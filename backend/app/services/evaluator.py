"""AI/ML Coding Agent Visual Reasoning and Diagram Benchmark Evaluator.

Evaluates coding agent diagram synthesis capabilities against labeled ground-truth
specifications and geometric containment constraints.
"""
import datetime as dt
import time
import uuid
from typing import Any, Dict, List
from app.models.schemas import (
    BenchmarkCase,
    BenchmarkRunItemResult,
    DiagramContent,
    EvaluationSummaryResponse,
)
from app.services.engine import EditorialEngine
from app.services.validator import DiagramValidator


def _bcase(cid: str, name: str, cat: str, dtype: str, prompt: str, title: str, eyebrow: str, data: dict, rules: list) -> BenchmarkCase:
    return BenchmarkCase(
        id=cid,
        name=name,
        category=cat,
        diagram_type=dtype,  # type: ignore
        prompt=prompt,
        spec={"title": title, "eyebrow": eyebrow, "data": data},
        expected_rules=rules,
    )


BENCHMARK_DATASET: List[BenchmarkCase] = [
    _bcase(
        "case-01-azure-aks", "Azure AKS Baseline Network Topology", "cloud_containment", "architecture_azure",
        "Design Azure AKS topology with private endpoint.", "AKS Production Cluster Topology", "CLOUD ARCHITECTURE",
        {"subscription": "Enterprise Sub", "resource_group": "Aks-RG", "vnet": "vnet-aks-10.240.0.0/16",
         "subnets": [{"name": "snet-aks", "nodes": [{"id": "vm1", "label": "AKS Nodes", "type": "compute", "ip": "10.240.0.10"}]},
                     {"name": "snet-pe", "nodes": [{"id": "pe-sql", "label": "pe-sql", "type": "private_endpoint", "ip": "10.240.4.15"}]}],
         "paas_services": [{"id": "sql1", "label": "Azure SQL", "target_pe": "pe-sql", "tier": "General Purpose"}]},
        ["containment.cloud_hierarchy_4level", "containment.paas_isolation", "containment.private_endpoint_linkage"]
    ),
    _bcase(
        "case-02-energy-treemap", "Global Clean Energy Generation Treemap", "dataviz", "treemap",
        "Proportional treemap of 2026 clean energy generation.", "Clean Energy Generation by Source", "DATA VISUALIZATION",
        {"items": [{"label": "Solar", "value": 1450}, {"label": "Wind", "value": 1180}, {"label": "Hydro", "value": 890}, {"label": "Nuclear", "value": 640}]},
        ["honest_data.treemap_positive_values", "skin.no_drop_shadows"]
    ),
    _bcase(
        "case-03-inference-sankey", "LLM Inference Compute Energy Sankey", "dataviz", "sankey",
        "Model cluster power dissipation through tensor parallel compute stages.", "GPU Cluster Energy Flow", "AI INFRASTRUCTURE",
        {"left_nodes": [{"id": "grid", "label": "Grid Feed", "value": 120}, {"id": "solar", "label": "Solar Canopy", "value": 30}],
         "right_nodes": [{"id": "tensor", "label": "Tensor Matrix", "value": 95}, {"id": "hbm", "label": "HBM Bus", "value": 25}, {"id": "cooling_dissipation", "label": "Thermal Cooling", "value": 30}]},
        ["honest_data.sankey_conservation_of_mass", "skin.no_drop_shadows"]
    ),
    _bcase(
        "case-04-model-slopegraph", "Model Optimization Slopegraph", "dataviz", "slopegraph",
        "Quantization benchmark metric improvements from FP16 to INT4 AWQ.", "Post-Training Quantization Impact", "MODEL EVALUATION",
        {"moment_a_label": "FP16", "moment_b_label": "INT4", "items": [{"label": "VRAM", "a": 96, "b": 24, "highlight": True}, {"label": "Throughput", "a": 32, "b": 88, "highlight": True}]},
        ["honest_data.slopegraph_items", "skin.no_drop_shadows"]
    ),
    _bcase(
        "case-05-rag-pipeline", "Hybrid RAG Retrieval Engine Flow", "ai_systems", "rag_pipeline",
        "Multi-stage hybrid RAG pipeline with cross-encoder reranking.", "Multi-Stage Hybrid RAG Architecture", "AGENT REASONING",
        {}, ["skin.no_drop_shadows", "skin.responsive_viewbox"]
    ),
    _bcase(
        "case-06-sbgn-egfr-cascade", "EGFR Signal Transduction SBGN Cascade", "biology", "sbgn_pd",
        "SBGN Process Description for EGFR dimerization.", "EGFR Receptor Dimerization Cascade", "SYSTEMS BIOLOGY",
        {"macromolecules": [{"id": "egf", "label": "EGF", "x": 80, "y": 140}, {"id": "egfr", "label": "EGFR", "x": 80, "y": 280}, {"id": "grb2", "label": "GRB2", "x": 620, "y": 210}],
         "complexes": [{"id": "dimer", "label": "2:2 Active Dimer", "x": 340, "y": 170, "w": 220, "h": 110}]},
        ["sbgn.species_declared", "skin.no_drop_shadows"]
    ),
    _bcase(
        "case-07-alignment-waffle", "Safety Alignment Distribution Waffle", "ai_safety", "waffle",
        "Waffle grid of red-team attack responses.", "Adversarial Prompt Evaluation", "AI SAFETY BENCHMARK",
        {"categories": [{"label": "Safe Refusal", "count": 68}, {"label": "Safe Fulfill", "count": 27}, {"label": "Flagged", "count": 5}]},
        ["honest_data.waffle_categories", "skin.no_drop_shadows"]
    ),
    _bcase(
        "case-08-model-swarm", "Open Weights Reasoning Beeswarm", "model_quality", "beeswarm",
        "1D distribution beeswarm of open weights reasoning scores.", "Mathematical Reasoning Benchmark", "MODEL QUALITY",
        {"samples": [{"val": 22, "label": "TinyLlama"}, {"val": 52, "label": "Mistral-7B"}, {"val": 88, "label": "DeepSeek"}, {"val": 93, "label": "Llama-3.1"}]},
        ["skin.no_drop_shadows", "skin.responsive_viewbox"]
    ),
    _bcase(
        "case-09-precision-recall-dumbbell", "Embedder Precision-Recall Dumbbell", "dataviz", "dumbbell",
        "Compare baseline vs fine-tuned domain embedder.", "Embedding Model Fine-Tuning Gains", "RETRIEVAL BENCHMARK",
        {"items": [{"label": "Code Search", "point_a": 48, "point_b": 89}, {"label": "Tech Docs", "point_a": 54, "point_b": 87}]},
        ["skin.no_drop_shadows", "skin.responsive_viewbox"]
    ),
    _bcase(
        "case-10-aws-vpc-isolation", "AWS Multi-AZ VPC Isolation", "cloud_containment", "architecture_aws",
        "Verify AWS 4-level containment hierarchy with private endpoint.", "AWS Production Multi-AZ VPC", "CLOUD ARCHITECTURE",
        {"subscription": "AWS Account 123", "resource_group": "us-east-1 RG", "vnet": "vpc-prod [10.0.0.0/16]",
         "subnets": [{"name": "snet-app", "nodes": [{"id": "ecs", "label": "ECS", "type": "compute", "ip": "10.0.1.50"}]},
                     {"name": "snet-vpce", "nodes": [{"id": "pe-s3", "label": "vpce-s3", "type": "private_endpoint", "ip": "10.0.10.12"}]}],
         "paas_services": [{"id": "s3", "label": "S3 Bucket", "target_pe": "pe-s3", "tier": "Standard"}]},
        ["containment.cloud_hierarchy_4level", "containment.paas_isolation"]
    ),
    _bcase(
        "case-11-context-scaling-slope", "Context Window Scaling Slopegraph", "model_quality", "slopegraph",
        "Needle-in-a-haystack retrieval accuracy at 8k vs 128k context.", "Needle Retrieval Across Context Lengths", "LONG CONTEXT BENCHMARK",
        {"moment_a_label": "8K", "moment_b_label": "128K", "items": [{"label": "Header Fact", "a": 99, "b": 98}, {"label": "Mid Distractor", "a": 97, "b": 92}]},
        ["honest_data.slopegraph_items"]
    ),
    _bcase(
        "case-12-datacenter-pue-sankey", "AI Datacenter Power Distribution", "dataviz", "sankey",
        "Track megawatt delivery from substation to GPU silicon.", "Dedicated Compute Facility Power Flow", "DATA CENTER EFFICIENCY",
        {"left_nodes": [{"id": "sub", "label": "Substation", "value": 45}, {"id": "bess", "label": "Battery Buffer", "value": 5}],
         "right_nodes": [{"id": "servers", "label": "OAM Racks", "value": 38}, {"id": "chillers", "label": "Water Loops", "value": 8}, {"id": "loss", "label": "Dissipation", "value": 4}]},
        ["honest_data.sankey_conservation_of_mass"]
    ),
    _bcase(
        "case-13-gpu-market-treemap", "AI Accelerator Architecture Distribution", "dataviz", "treemap",
        "Compute capacity share by microarchitecture tier.", "Compute Accelerator Distribution", "HARDWARE FLEET",
        {"items": [{"label": "Blackwell B200", "value": 540}, {"label": "Hopper H100", "value": 380}, {"label": "Ampere A100", "value": 160}]},
        ["honest_data.treemap_positive_values"]
    ),
    _bcase(
        "case-14-agent-task-waffle", "Agent Autonomous Task Success Waffle", "ai_systems", "waffle",
        "Autonomous software engineering benchmark evaluation.", "Autonomous Issue Resolution Pass Rate", "SWE-BENCH LITE",
        {"categories": [{"label": "Verified Resolution", "count": 52}, {"label": "Partial Pass", "count": 28}, {"label": "Error", "count": 20}]},
        ["honest_data.waffle_categories"]
    ),
    _bcase(
        "case-15-latency-jitter-beeswarm", "Token Generation Inter-Arrival Time", "model_quality", "beeswarm",
        "Token inter-arrival latency distribution across engines.", "Time-Per-Output-Token Distribution", "STREAMING INFERENCE",
        {"samples": [{"val": 14, "label": "vLLM"}, {"val": 16, "label": "TGI"}, {"val": 22, "label": "SGLang"}, {"val": 35, "label": "TensorRT"}]},
        ["skin.no_drop_shadows"]
    ),
    _bcase(
        "case-16-mapk-pathway-sbgn", "MAPK Cascade Signaling Pathway", "biology", "sbgn_pd",
        "SBGN Process Description of the RAF-MEK-ERK cascade.", "MAPK Core Phosphorylation Cascade", "MOLECULAR BIOLOGY",
        {"macromolecules": [{"id": "ras", "label": "RAS:GTP", "x": 90, "y": 140}, {"id": "raf", "label": "RAF-1", "x": 90, "y": 280}, {"id": "mek", "label": "MEK1/2", "x": 600, "y": 210}],
         "complexes": [{"id": "p-raf", "label": "Phospho-RAF Dimer", "x": 340, "y": 180, "w": 200, "h": 100}]},
        ["sbgn.species_declared"]
    ),
    _bcase(
        "case-17-embedding-compression-dumbbell", "Vector Quantization Recall Tradeoff", "dataviz", "dumbbell",
        "Evaluate Scalar Quantization vs full FP32.", "Vector Compression Recall Tradeoffs", "VECTOR DATABASE BENCHMARK",
        {"items": [{"label": "BioMed Recall@100", "point_a": 96, "point_b": 94}, {"label": "10-K Retrieval", "point_a": 92, "point_b": 89}]},
        ["skin.no_drop_shadows"]
    ),
    _bcase(
        "case-18-azure-hub-spoke", "Azure Secure Enterprise Hub-and-Spoke", "cloud_containment", "architecture_azure",
        "Azure hub and spoke architecture with Azure Firewall.", "Enterprise Hub-and-Spoke Secure VNet", "NETWORK INFRASTRUCTURE",
        {"subscription": "Connectivity Sub", "resource_group": "rg-network-hub", "vnet": "vnet-hub-10.100.0.0/16",
         "subnets": [{"name": "AzureFirewallSubnet", "nodes": [{"id": "fw", "label": "Firewall", "type": "gateway", "ip": "10.100.1.4"}]},
                     {"name": "snet-bastion", "nodes": [{"id": "pe-kv", "label": "pe-keyvault", "type": "private_endpoint", "ip": "10.100.2.10"}]}],
         "paas_services": [{"id": "kv", "label": "Key Vault", "target_pe": "pe-kv", "tier": "Premium"}]},
        ["containment.cloud_hierarchy_4level", "containment.paas_isolation"]
    ),
    _bcase(
        "case-19-agentic-rag-router", "Agentic Self-Correcting RAG Flow", "ai_systems", "rag_pipeline",
        "Design self-correcting RAG flow with query router.", "Self-Correcting Corrective RAG Pipeline", "AGENT CONTROL FLOW",
        {}, ["skin.responsive_viewbox"]
    ),
    _bcase(
        "case-20-energy-capacity-treemap", "Global Grid Storage Battery Chemistries", "dataviz", "treemap",
        "Proportional area representation of battery storage.", "Stationary Battery Storage Deployments (GWh)", "GRID OBSERVABILITY",
        {"items": [{"label": "LFP", "value": 720}, {"label": "NMC", "value": 310}, {"label": "Sodium-Ion", "value": 95}]},
        ["honest_data.treemap_positive_values"]
    ),
]


class BenchmarkEvaluator:
    """Evaluates agent-generated diagrams against deterministic ground-truth requirements."""

    def __init__(self, engine: EditorialEngine = None):
        self.engine = engine or EditorialEngine()

    def run_suite(self, cases: List[BenchmarkCase] = None) -> EvaluationSummaryResponse:
        active_cases = cases or BENCHMARK_DATASET
        results: List[BenchmarkRunItemResult] = []

        containment_passed = 0
        containment_total = 0
        honest_passed = 0
        honest_total = 0
        total_render_ms = 0.0

        for case in active_cases:
            case_start = time.perf_counter()
            content = DiagramContent(
                eyebrow=case.spec.get("eyebrow"),
                title=case.spec.get("title", case.name),
                subtitle=case.spec.get("subtitle"),
                source=case.spec.get("source"),
                data=case.spec.get("data", {}),
            )

            render_resp = self.engine.render(case.diagram_type, content)
            case_render_ms = (time.perf_counter() - case_start) * 1000.0
            total_render_ms += case_render_ms

            report = DiagramValidator.validate(case.diagram_type, content, render_resp.svg)
            rules_met = all(r in report.passed_rules for r in case.expected_rules)
            passed = report.valid and rules_met

            if case.diagram_type in {"architecture_azure", "architecture_aws"}:
                containment_total += 1
                if report.containment_compliant:
                    containment_passed += 1

            honest_total += 1
            if report.honest_data_compliant:
                honest_passed += 1

            results.append(
                BenchmarkRunItemResult(
                    case_id=case.id,
                    name=case.name,
                    diagram_type=case.diagram_type,
                    passed=passed,
                    validation=report,
                    render_time_ms=round(case_render_ms, 2),
                    error=None if passed else f"Failed checks: {[i.rule for i in report.issues]}",
                )
            )

        passed_count = sum(1 for r in results if r.passed)
        total_count = len(results)
        accuracy = (passed_count / total_count) if total_count > 0 else 0.0
        containment_rate = (containment_passed / containment_total) if containment_total > 0 else 1.0
        honest_rate = (honest_passed / honest_total) if honest_total > 0 else 1.0
        avg_latency = (total_render_ms / total_count) if total_count > 0 else 0.0

        return EvaluationSummaryResponse(
            run_id=str(uuid.uuid4()),
            timestamp=dt.datetime.now(dt.timezone.utc),
            total_cases=total_count,
            passed_cases=passed_count,
            accuracy_rate=round(accuracy, 4),
            containment_compliance_rate=round(containment_rate, 4),
            honest_data_rate=round(honest_rate, 4),
            avg_render_latency_ms=round(avg_latency, 2),
            cases=results,
        )


if __name__ == "__main__":
    evaluator = BenchmarkEvaluator()
    summary = evaluator.run_suite()
    print("=" * 72)
    print("ORBIT WORKBENCH | AI/ML CODING AGENT BENCHMARK EVALUATION")
    print("=" * 72)
    print(f"Total Benchmark Cases Evaluated : {summary.total_cases}")
    print(f"Passed Cases                    : {summary.passed_cases}")
    print(f"Spec Accuracy Rate              : {summary.accuracy_rate * 100:.1f}%")
    print(f"Containment Compliance Rate     : {summary.containment_compliance_rate * 100:.1f}%")
    print(f"Honest-Data Compliance Rate     : {summary.honest_data_rate * 100:.1f}%")
    print(f"Avg Render Latency (ms)         : {summary.avg_render_latency_ms:.2f} ms")
    print("-" * 72)
    for c in summary.cases:
        status_sym = "[PASS]" if c.passed else "[FAIL]"
        print(f"{status_sym} {c.case_id:<28} | {c.diagram_type:<20} | {c.render_time_ms:>5.1f}ms | {c.name}")
    print("=" * 72)
