/**
 * TypeScript API contracts matching backend schemas.
 */

export type DiagramType =
  | 'architecture_azure'
  | 'architecture_aws'
  | 'treemap'
  | 'sankey'
  | 'slopegraph'
  | 'dumbbell'
  | 'waffle'
  | 'beeswarm'
  | 'sbgn_pd'
  | 'rag_pipeline';

export type DiagramTheme =
  | 'editorial_light'
  | 'editorial_dark'
  | 'blueprint'
  | 'warm_paper';

export interface DiagramContent {
  eyebrow?: string;
  title: string;
  subtitle?: string;
  footnote?: string;
  source?: string;
  data: Record<string, any>;
  options?: Record<string, any>;
}

export interface DiagramItem {
  id: string;
  name: string;
  diagram_type: DiagramType;
  theme: DiagramTheme;
  content: DiagramContent;
  created_at: string;
  updated_at: string;
  created_by: string;
}

export interface ValidationIssue {
  rule: string;
  severity: 'error' | 'warning' | 'info';
  message: string;
  element_id?: string;
}

export interface ValidationReport {
  valid: boolean;
  diagram_type: DiagramType;
  total_checks: number;
  issues: ValidationIssue[];
  passed_rules: string[];
  honest_data_compliant: boolean;
  containment_compliant: boolean;
  skin_compliant: boolean;
}

export interface RenderResult {
  diagram_type: DiagramType;
  theme: DiagramTheme;
  svg: string;
  html: string;
  element_count: number;
  render_time_ms: number;
}

export interface BenchmarkCaseResult {
  case_id: string;
  name: string;
  diagram_type: DiagramType;
  passed: boolean;
  validation: ValidationReport;
  render_time_ms: number;
  error?: string;
}

export interface EvaluationSummary {
  run_id: string;
  timestamp: string;
  total_cases: number;
  passed_cases: number;
  accuracy_rate: number;
  containment_compliance_rate: number;
  honest_data_rate: number;
  avg_render_latency_ms: number;
  cases: BenchmarkCaseResult[];
}

export interface UserProfile {
  user_id: string;
  username: string;
  email?: string;
  roles: string[];
  is_demo: boolean;
}

export interface AuditLog {
  id: number;
  timestamp: string;
  user_id: string;
  action: string;
  resource_type: string;
  resource_id: string;
  details: Record<string, any>;
}
