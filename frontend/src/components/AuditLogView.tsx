import React, { useState, useEffect } from 'react';
import { AuditLog } from '../types/api';
import { api } from '../services/api';

export const AuditLogView: React.FC = () => {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchLogs = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.listAuditLogs();
      setLogs(res.items);
    } catch (err: any) {
      setError(`Failed to load audit logs: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  return (
    <div className="audit-container">
      <div className="audit-header">
        <div>
          <h2 className="section-heading">Security Audit Trail</h2>
          <p className="section-sub">Immutable transaction log recording diagram modifications and access events.</p>
        </div>
        <button onClick={fetchLogs} disabled={loading} className="btn btn-secondary">
          Refresh Logs
        </button>
      </div>

      {error && <div className="notice-banner error">{error}</div>}

      <div className="audit-table-wrap">
        <table className="audit-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>UTC Timestamp</th>
              <th>User ID</th>
              <th>Action</th>
              <th>Resource</th>
              <th>Details</th>
            </tr>
          </thead>
          <tbody>
            {logs.map((log) => (
              <tr key={log.id}>
                <td className="log-id">#{log.id}</td>
                <td className="log-time">{new Date(log.timestamp).toISOString()}</td>
                <td className="log-user">{log.user_id}</td>
                <td>
                  <span className="action-badge">{log.action}</span>
                </td>
                <td className="log-res">{log.resource_type}:{log.resource_id.slice(0, 8)}</td>
                <td className="log-details">{JSON.stringify(log.details)}</td>
              </tr>
            ))}
            {logs.length === 0 && !loading && (
              <tr>
                <td colSpan={6} className="text-center">
                  No audit log records recorded yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
