/**
 * Typed API client for Orbit Workbench backend.
 */

import {
  AuditLog,
  DiagramContent,
  DiagramItem,
  DiagramTheme,
  DiagramType,
  EvaluationSummary,
  RenderResult,
  ValidationReport,
} from '../types/api';
import { authService } from './auth';

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = authService.getToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(path, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const errorText = await response.text();
    let message = `API Request failed: ${response.statusText}`;
    try {
      const errJson = JSON.parse(errorText);
      message = errJson.detail || message;
    } catch {
      // Raw text fallback
    }
    throw new Error(message);
  }

  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}

export const api = {
  async getHealth(): Promise<Record<string, any>> {
    return request('/api/health');
  },

  async listDiagrams(type?: string): Promise<{ items: DiagramItem[]; total: number }> {
    const query = type ? `?diagram_type=${encodeURIComponent(type)}` : '';
    return request(`/api/diagrams${query}`);
  },

  async getDiagram(id: string): Promise<DiagramItem> {
    return request(`/api/diagrams/${id}`);
  },

  async createDiagram(data: {
    name: string;
    diagram_type: DiagramType;
    theme: DiagramTheme;
    content: DiagramContent;
  }): Promise<DiagramItem> {
    return request('/api/diagrams', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async updateDiagram(
    id: string,
    data: Partial<{
      name: string;
      diagram_type: DiagramType;
      theme: DiagramTheme;
      content: DiagramContent;
    }>
  ): Promise<DiagramItem> {
    return request(`/api/diagrams/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  async deleteDiagram(id: string): Promise<void> {
    return request(`/api/diagrams/${id}`, {
      method: 'DELETE',
    });
  },

  async renderLive(payload: {
    diagram_type: DiagramType;
    theme: DiagramTheme;
    content: DiagramContent;
  }): Promise<RenderResult> {
    return request('/api/diagrams/render', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async validateLive(payload: {
    diagram_type: DiagramType;
    theme: DiagramTheme;
    content: DiagramContent;
  }): Promise<ValidationReport> {
    return request('/api/diagrams/validate', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async explainDiagram(payload: {
    spec: DiagramContent;
    question?: string;
  }): Promise<{ explanation: string; provider: string; model: string }> {
    return request('/api/diagrams/explain', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async runEvaluation(): Promise<EvaluationSummary> {
    return request('/api/evaluation/run', {
      method: 'POST',
    });
  },

  async getEvaluationHistory(): Promise<any[]> {
    return request('/api/evaluation/history');
  },

  async listAuditLogs(): Promise<{ items: AuditLog[]; total: number }> {
    return request('/api/audit');
  },

  async getAuthConfig(): Promise<Record<string, any>> {
    return request('/api/auth/config');
  },
};
