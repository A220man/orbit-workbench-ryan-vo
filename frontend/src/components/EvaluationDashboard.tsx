import React, { useState } from 'react';
import { EvaluationSummary, BenchmarkCaseResult } from '../types/api';
import { api } from '../services/api';

export const EvaluationDashboard: React.FC = () => {
  const [summary, setSummary] = useState<EvaluationSummary | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [selectedCase, setSelectedCase] = useState<BenchmarkCaseResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleRunSuite = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.runEvaluation();
      setSummary(res);
      if (res.cases.length > 0) {
        setSelectedCase(res.cases[0]);
      }
    } catch (err: any) {
      setError(`Evaluation failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="eval-container">
      <div className="eval-header-section">
        <div>
          <h2 className="section-heading">AI/ML Coding Agent Visual Reasoning Benchmark</h2>
          <p className="section-sub">
            Evaluates 20 labeled diagram prompts covering Azure network containment, honest data encodings, and systems biology notation.
          </p>
        </div>
        <button
          onClick={handleRunSuite}
          disabled={loading}
          className="btn btn-primary run-eval-btn"
        >
          {loading ? 'Evaluating Benchmark...' : 'Execute Evaluation Suite'}
        </button>
      </div>

      {error && <div className="notice-banner error">{error}</div>}

      {summary && (
        <>
          <div className="metrics-grid">
            <div className="metric-card">
              <span className="metric-label">Spec Accuracy Rate</span>
              <span className="metric-value">{`${(summary.accuracy_rate * 100).toFixed(1)}%`}</span>
              <span className="metric-sub">{summary.passed_cases} / {summary.total_cases} Passed</span>
            </div>
            <div className="metric-card">
              <span className="metric-label">Containment Compliance</span>
              <span className="metric-value">{`${(summary.containment_compliance_rate * 100).toFixed(1)}%`}</span>
              <span className="metric-sub">PaaS &amp; VNet Hierarchy Rules</span>
            </div>
            <div className="metric-card">
              <span className="metric-label">Honest-Data Compliance</span>
              <span className="metric-value">{`${(summary.honest_data_rate * 100).toFixed(1)}%`}</span>
              <span className="metric-sub">Mass &amp; Area Encodings</span>
            </div>
            <div className="metric-card">
              <span className="metric-label">Avg Render Latency</span>
              <span className="metric-value">{summary.avg_render_latency_ms.toFixed(2)} ms</span>
              <span className="metric-sub">Deterministic Vector Engine</span>
            </div>
          </div>

          <div className="cases-layout">
            <div className="cases-list-panel">
              <h3 className="sub-heading">Benchmark Cases</h3>
              <div className="cases-table-wrap">
                <table className="cases-table">
                  <thead>
                    <tr>
                      <th>Status</th>
                      <th>Case ID</th>
                      <th>Type</th>
                      <th>Latency</th>
                    </tr>
                  </thead>
                  <tbody>
                    {summary.cases.map((c) => (
                      <tr
                        key={c.case_id}
                        className={selectedCase?.case_id === c.case_id ? 'selected-row' : ''}
                        onClick={() => setSelectedCase(c)}
                      >
                        <td>
                          <span className={`status-badge ${c.passed ? 'pass' : 'fail'}`}>
                            {c.passed ? 'PASS' : 'FAIL'}
                          </span>
                        </td>
                        <td className="case-id-cell">{c.case_id}</td>
                        <td className="type-cell">{c.diagram_type}</td>
                        <td className="time-cell">{c.render_time_ms}ms</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {selectedCase && (
              <div className="case-detail-panel">
                <div className="case-detail-header">
                  <h3>{selectedCase.name}</h3>
                  <span className="tag-type">{selectedCase.diagram_type}</span>
                </div>
                <div className="case-detail-body">
                  <div className="detail-item">
                    <strong>Validation Status:</strong>{' '}
                    <span className={selectedCase.passed ? 'text-green' : 'text-red'}>
                      {selectedCase.passed ? 'All Compliance Gates Passed' : 'Violations Detected'}
                    </span>
                  </div>
                  <div className="detail-item">
                    <strong>Render Latency:</strong> {selectedCase.render_time_ms} ms
                  </div>
                  <div className="detail-item">
                    <strong>Passed Rules ({selectedCase.validation.passed_rules.length}):</strong>
                    <ul className="rule-tags">
                      {selectedCase.validation.passed_rules.map((r, i) => (
                        <li key={i} className="rule-tag">
                          {r}
                        </li>
                      ))}
                    </ul>
                  </div>
                  {selectedCase.validation.issues.length > 0 && (
                    <div className="detail-item">
                      <strong>Detected Issues:</strong>
                      <ul className="issue-list">
                        {selectedCase.validation.issues.map((iss, i) => (
                          <li key={i} className="issue-tag">
                            [{iss.rule}] {iss.message}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </>
      )}

      {!summary && !loading && (
        <div className="empty-state">
          <p>No benchmark run executed yet. Click "Execute Evaluation Suite" above to benchmark the diagram compiler.</p>
        </div>
      )}
    </div>
  );
};
