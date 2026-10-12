import React, { useState, useEffect } from 'react';
import {
  DiagramContent,
  DiagramTheme,
  DiagramType,
  RenderResult,
  ValidationReport,
} from '../types/api';
import { api } from '../services/api';

const PRESETS: Record<string, { type: DiagramType; content: DiagramContent }> = {
  azure_aks: {
    type: 'architecture_azure',
    content: {
      eyebrow: 'CLOUD CONTAINMENT GRAMMAR',
      title: 'Azure AKS with Isolated PaaS SQL',
      subtitle: 'Demonstrates 4-level network hierarchy and PaaS private endpoint placement',
      data: {
        subscription: 'Production Subscription [sub-prod-01]',
        resource_group: 'Aks-Production-RG',
        vnet: 'vnet-aks-hub-10.200.0.0/16',
        subnets: [
          {
            name: 'snet-aks-nodes [10.200.1.0/24]',
            nodes: [{ id: 'aks1', label: 'AKS System Node Pool (VMSS)', type: 'compute', ip: '10.200.1.10' }],
          },
          {
            name: 'snet-pe [10.200.2.0/24]',
            nodes: [{ id: 'pe-sql', label: 'pe-sqldb (Private Endpoint)', type: 'private_endpoint', ip: '10.200.2.80' }],
          },
        ],
        paas_services: [
          { id: 'sql1', label: 'Azure SQL Managed Database', target_pe: 'pe-sql', tier: 'Business Critical' },
        ],
      },
    },
  },
  treemap_energy: {
    type: 'treemap',
    content: {
      eyebrow: 'PROPORTIONAL DATA VISUALIZATION',
      title: 'Clean Energy Generation Capacity',
      subtitle: 'Honest area encoding without log compression',
      source: 'Our World In Data (OWID 2026)',
      data: {
        items: [
          {"label": "Solar Photovoltaic", "value": 1450, "color_alpha": 0.9},
          {"label": "Wind Turbines", "value": 1180, "color_alpha": 0.75},
          {"label": "Hydroelectric", "value": 890, "color_alpha": 0.6},
          {"label": "Nuclear Fission", "value": 640, "color_alpha": 0.45},
          {"label": "Geothermal", "value": 210, "color_alpha": 0.3},
        ],
      },
    },
  },
  sankey_compute: {
    type: 'sankey',
    content: {
      eyebrow: 'AI INFRASTRUCTURE',
      title: 'GPU Cluster Energy Dissipation Flow',
      subtitle: 'Bipartite ribbon routing with conservation of flow',
      data: {
        left_nodes: [
          { id: 'grid', label: 'High-Voltage Grid', value: 120 },
          { id: 'solar', label: 'Onsite Solar', value: 30 },
        ],
        right_nodes: [
          { id: 'compute', label: 'Matrix FLOPS', value: 95 },
          { id: 'hbm', label: 'HBM3e Memory', value: 25 },
          { id: 'cooling', label: 'Thermal Cooling', value: 30 },
        ],
      },
    },
  },
  slope_quant: {
    type: 'slopegraph',
    content: {
      eyebrow: 'MODEL BENCHMARK',
      title: 'Post-Training Quantization Trajectory',
      subtitle: 'FP16 Baseline vs INT4 AWQ metrics',
      data: {
        moment_a_label: 'FP16 Baseline',
        moment_b_label: 'INT4 AWQ Target',
        items: [
          { label: 'Throughput (tok/s)', a: 34, b: 89, highlight: true },
          { label: 'VRAM Usage (GB)', a: 80, b: 24, highlight: true },
          { label: 'MMLU Quality Score', a: 86, b: 84, highlight: false },
        ],
      },
    },
  },
  sbgn_cascade: {
    type: 'sbgn_pd',
    content: {
      eyebrow: 'SYSTEMS BIOLOGY',
      title: 'EGFR Biochemical Dimerization',
      subtitle: 'Process Description standard layout with catalytic arcs',
      data: {
        macromolecules: [
          { id: 'egf', label: 'EGF Ligand', x: 80, y: 140 },
          { id: 'egfr', label: 'EGFR Monomer', x: 80, y: 280 },
          { id: 'grb2', label: 'GRB2 Adaptor', x: 620, y: 210 },
        ],
        complexes: [
          { id: 'dimer', label: 'Active 2:2 Dimer', x: 340, y: 170, w: 220, h: 110 },
        ],
      },
    },
  },
};

interface DiagramEditorProps {
  theme: DiagramTheme;
}

export const DiagramEditor: React.FC<DiagramEditorProps> = ({ theme }) => {
  const [selectedPreset, setSelectedPreset] = useState<string>('azure_aks');
  const [diagramType, setDiagramType] = useState<DiagramType>('architecture_azure');
  const [specJson, setSpecJson] = useState<string>(
    JSON.stringify(PRESETS['azure_aks'].content, null, 2)
  );
  const [rendered, setRendered] = useState<RenderResult | null>(null);
  const [validation, setValidation] = useState<ValidationReport | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [explanation, setExplanation] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const handlePresetSelect = (key: string) => {
    setSelectedPreset(key);
    const p = PRESETS[key];
    if (p) {
      setDiagramType(p.type);
      setSpecJson(JSON.stringify(p.content, null, 2));
    }
  };

  const handleCompile = async () => {
    try {
      setLoading(true);
      setNotice(null);
      const parsedContent = JSON.parse(specJson);
      const payload = {
        diagram_type: diagramType,
        theme,
        content: parsedContent,
      };

      const [renderRes, valRes] = await Promise.all([
        api.renderLive(payload),
        api.validateLive(payload),
      ]);

      setRendered(renderRes);
      setValidation(valRes);
    } catch (err: any) {
      setNotice(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setLoading(true);
      const parsedContent = JSON.parse(specJson);
      const result = await api.createDiagram({
        name: parsedContent.title || 'Saved Diagram',
        diagram_type: diagramType,
        theme,
        content: parsedContent,
      });
      setNotice(`Saved successfully as '${result.name}' (ID: ${result.id.slice(0, 8)})`);
    } catch (err: any) {
      setNotice(`Save failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleExplain = async () => {
    try {
      setLoading(true);
      const parsedContent = JSON.parse(specJson);
      const res = await api.explainDiagram({ spec: parsedContent });
      setExplanation(res.explanation);
    } catch (err: any) {
      setNotice(`Advisory error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = (format: 'svg' | 'html') => {
    if (!rendered) return;
    const blob = new Blob([format === 'svg' ? rendered.svg : rendered.html], {
      type: format === 'svg' ? 'image/svg+xml' : 'text/html',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `diagram.${format}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  useEffect(() => {
    handleCompile();
  }, [theme]);

  return (
    <div className="editor-layout">
      <div className="editor-sidebar">
        <div className="control-group">
          <label className="control-label">Domain Presets</label>
          <select
            value={selectedPreset}
            onChange={(e) => handlePresetSelect(e.target.value)}
            className="input-select"
            aria-label="Domain Presets"
          >
            <option value="azure_aks">Azure AKS Containment</option>
            <option value="treemap_energy">Clean Energy Treemap</option>
            <option value="sankey_compute">GPU Cluster Energy Sankey</option>
            <option value="slope_quant">Quantization Slopegraph</option>
            <option value="sbgn_cascade">EGFR SBGN Pathway</option>
          </select>
        </div>

        <div className="control-group">
          <label className="control-label">Diagram Type</label>
          <select
            value={diagramType}
            onChange={(e) => setDiagramType(e.target.value as DiagramType)}
            className="input-select"
          >
            <option value="architecture_azure">Azure Architecture</option>
            <option value="architecture_aws">AWS Architecture</option>
            <option value="treemap">Treemap (Proportion)</option>
            <option value="sankey">Sankey (Flow)</option>
            <option value="slopegraph">Slopegraph (Rank Change)</option>
            <option value="dumbbell">Dumbbell (Paired Values)</option>
            <option value="waffle">Waffle (Part-of-Whole)</option>
            <option value="beeswarm">Beeswarm (Distribution)</option>
            <option value="sbgn_pd">SBGN Process Description</option>
            <option value="rag_pipeline">RAG Retrieval Flow</option>
          </select>
        </div>

        <div className="control-group flex-1">
          <label className="control-label">Specification JSON</label>
          <textarea
            value={specJson}
            onChange={(e) => setSpecJson(e.target.value)}
            className="code-textarea"
            rows={16}
            aria-label="Specification JSON"
          />
        </div>

        <div className="action-buttons">
          <button onClick={handleCompile} disabled={loading} className="btn btn-primary">
            Compile &amp; Render
          </button>
          <button onClick={handleSave} disabled={loading} className="btn btn-secondary">
            Save to Catalog
          </button>
          <button onClick={handleExplain} disabled={loading} className="btn btn-outline">
            Advisory Review
          </button>
        </div>

        {notice && <div className="notice-banner">{notice}</div>}

        {validation && (
          <div className={`validation-box ${validation.valid ? 'valid' : 'invalid'}`}>
            <div className="val-header">
              <span className="val-title">Compliance Gate</span>
              <span className={`val-tag ${validation.valid ? 'pass' : 'fail'}`}>
                {validation.valid ? 'PASSED' : 'VIOLATION'}
              </span>
            </div>
            <div className="val-rules">
              <span className={validation.containment_compliant ? 'rule-ok' : 'rule-bad'}>
                ✓ Containment
              </span>
              <span className={validation.honest_data_compliant ? 'rule-ok' : 'rule-bad'}>
                ✓ Honest Data
              </span>
              <span className={validation.skin_compliant ? 'rule-ok' : 'rule-bad'}>
                ✓ Skin Linter
              </span>
            </div>
            {validation.issues.length > 0 && (
              <ul className="issues-list">
                {validation.issues.map((i, idx) => (
                  <li key={idx} className={`issue-item ${i.severity}`}>
                    <strong>[{i.rule}]</strong> {i.message}
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </div>

      <div className="editor-preview-area">
        <div className="preview-toolbar">
          <span className="preview-meta">
            {rendered ? `${rendered.element_count} vector elements · ${rendered.render_time_ms}ms render latency` : 'Ready to compile'}
          </span>
          <div className="export-actions">
            <button onClick={() => handleDownload('svg')} disabled={!rendered} className="btn-icon">
              Export SVG
            </button>
            <button onClick={() => handleDownload('html')} disabled={!rendered} className="btn-icon">
              Export HTML
            </button>
          </div>
        </div>

        <div className="preview-stage">
          {rendered ? (
            <div
              className="svg-display"
              dangerouslySetInnerHTML={{ __html: rendered.svg }}
            />
          ) : (
            <div className="empty-preview">
              <p>Click "Compile &amp; Render" to synthesize vector diagram</p>
            </div>
          )}
        </div>

        {explanation && (
          <div className="explanation-drawer">
            <div className="drawer-header">
              <h4>Advisory Explanation (LLM Grounded)</h4>
              <button onClick={() => setExplanation(null)} className="close-btn">×</button>
            </div>
            <p className="drawer-text">{explanation}</p>
          </div>
        )}
      </div>
    </div>
  );
};
