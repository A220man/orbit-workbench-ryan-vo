import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import App from './App';
import { api } from './services/api';

describe('Orbit Workbench User Interface', () => {
  beforeEach(() => {
    vi.restoreAllMocks();

    // Mock global fetch for auth init
    vi.spyOn(window, 'fetch').mockImplementation(async (url: any) => {
      const urlStr = String(url);
      if (urlStr.includes('/api/auth/demo-login')) {
        return {
          ok: true,
          status: 200,
          json: async () => ({
            access_token: 'mock-jwt-token-analyst',
            user_id: 'demo-analyst',
            roles: ['analyst', 'viewer'],
            expires_in_minutes: 120,
          }),
        } as any;
      }
      if (urlStr.includes('/api/diagrams/render')) {
        return {
          ok: true,
          status: 200,
          json: async () => ({
            diagram_type: 'architecture_azure',
            theme: 'editorial_light',
            svg: '<svg viewBox="0 0 100 100"><rect width="100" height="100"/></svg>',
            html: '<!DOCTYPE html><html><body></body></html>',
            element_count: 12,
            render_time_ms: 0.5,
          }),
        } as any;
      }
      if (urlStr.includes('/api/diagrams/validate')) {
        return {
          ok: true,
          status: 200,
          json: async () => ({
            valid: true,
            diagram_type: 'architecture_azure',
            total_checks: 5,
            issues: [],
            passed_rules: ['containment.cloud_hierarchy_4level', 'skin.no_drop_shadows'],
            honest_data_compliant: true,
            containment_compliant: true,
            skin_compliant: true,
          }),
        } as any;
      }
      if (urlStr.includes('/api/audit')) {
        return {
          ok: true,
          status: 200,
          json: async () => ({
            items: [
              {
                id: 1,
                timestamp: '2026-10-12T07:00:00Z',
                user_id: 'demo-analyst',
                action: 'CREATE_DIAGRAM',
                resource_type: 'diagram',
                resource_id: 'diag-12345678',
                details: { name: 'Test' },
              },
            ],
            total: 1,
          }),
        } as any;
      }
      return {
        ok: true,
        status: 200,
        json: async () => ({}),
      } as any;
    });
  });

  it('renders application brand, studio editor, and initial compliance status', async () => {
    render(<App />);
    expect(screen.getByText('Orbit Workbench')).toBeInTheDocument();
    expect(screen.getByText('Studio Editor')).toBeInTheDocument();
    expect(screen.getByText('Agent Benchmarks')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('Compliance Gate')).toBeInTheDocument();
      expect(screen.getByText('PASSED')).toBeInTheDocument();
    });
  });

  it('allows switching navigation tabs to Agent Benchmarks and Audit Trail', async () => {
    render(<App />);

    const benchmarkTab = screen.getByText('Agent Benchmarks');
    fireEvent.click(benchmarkTab);

    expect(screen.getByText('AI/ML Coding Agent Visual Reasoning Benchmark')).toBeInTheDocument();
    expect(screen.getByText('Execute Evaluation Suite')).toBeInTheDocument();

    const auditTab = screen.getByText('Audit Trail');
    fireEvent.click(auditTab);

    expect(screen.getByText('Security Audit Trail')).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByText('CREATE_DIAGRAM')).toBeInTheDocument();
    });
  });

  it('supports role switching and preset selection workflow', async () => {
    render(<App />);

    // Click Admin role switcher
    const adminBtn = screen.getByTitle('Switch to Admin Role');
    fireEvent.click(adminBtn);

    // Switch to Clean Energy Treemap preset
    const presetSelect = screen.getByLabelText(/domain presets/i);
    fireEvent.change(presetSelect, { target: { value: 'treemap_energy' } });
    expect(presetSelect).toHaveValue('treemap_energy');

    // Click compile
    const compileBtn = screen.getByText('Compile & Render');
    fireEvent.click(compileBtn);

    await waitFor(() => {
      expect(screen.getByText('Compliance Gate')).toBeInTheDocument();
    });
  });

  it('executes agent evaluation benchmark and displays accuracy metrics', async () => {
    vi.spyOn(api, 'runEvaluation').mockResolvedValueOnce({
      run_id: 'run-99',
      timestamp: '2026-10-12T07:15:00Z',
      total_cases: 20,
      passed_cases: 20,
      accuracy_rate: 1.0,
      containment_compliance_rate: 1.0,
      honest_data_rate: 1.0,
      avg_render_latency_ms: 0.08,
      cases: [
        {
          case_id: 'case-01-azure-aks',
          name: 'Azure AKS Baseline Network Topology',
          diagram_type: 'architecture_azure',
          passed: true,
          validation: {
            valid: true,
            diagram_type: 'architecture_azure',
            total_checks: 3,
            issues: [],
            passed_rules: ['containment.cloud_hierarchy_4level'],
            honest_data_compliant: true,
            containment_compliant: true,
            skin_compliant: true,
          },
          render_time_ms: 0.1,
        },
      ],
    });

    render(<App />);
    const benchmarkTab = screen.getByText('Agent Benchmarks');
    fireEvent.click(benchmarkTab);

    const runBtn = screen.getByText('Execute Evaluation Suite');
    fireEvent.click(runBtn);

    await waitFor(() => {
      const percentages = screen.getAllByText('100.0%');
      expect(percentages.length).toBeGreaterThan(0);
      expect(screen.getByText('20 / 20 Passed')).toBeInTheDocument();
      expect(screen.getByText('Azure AKS Baseline Network Topology')).toBeInTheDocument();
    });
  });
});
