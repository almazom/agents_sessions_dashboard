'use client';

import { useEffect, useState } from 'react';
import { api, Session, Metrics } from '@/lib/api';
import SessionCard from '@/components/SessionCard';
import MetricsPanel from '@/components/MetricsPanel';

export default function Dashboard() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'active' | 'completed' | 'error'>('all');
  const [agentFilter, setAgentFilter] = useState<string>('all');

  // Загрузка данных
  useEffect(() => {
    loadData();
  }, [filter, agentFilter]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [sessionsRes, metricsRes] = await Promise.all([
        api.getSessions({
          status: filter === 'all' ? undefined : filter,
          agent: agentFilter === 'all' ? undefined : agentFilter,
          limit: 100,
        }),
        api.getMetrics(),
      ]);
      setSessions(sessionsRes.sessions);
      setMetrics(metricsRes.data);
    } catch (error) {
      console.error('Ошибка загрузки:', error);
    } finally {
      setLoading(false);
    }
  };

  // Группировка сессий по статусу
  const activeSessions = sessions.filter(s => s.status === 'active');
  const completedSessions = sessions.filter(s => s.status === 'completed' || s.status === 'paused');
  const errorSessions = sessions.filter(s => s.status === 'error');

  return (
    <main className="min-h-screen p-6">
      {/* Header */}
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-nexus-800">
          🤖 Agent Nexus
        </h1>
        <p className="text-nexus-500 mt-1">
          Мониторинг AI агентов в реальном времени
        </p>
      </header>

      {/* Metrics */}
      {metrics && <MetricsPanel metrics={metrics} />}

      {/* Filters */}
      <div className="flex gap-4 mb-6">
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value as any)}
          className="px-4 py-2 rounded-lg border border-nexus-200 bg-white"
        >
          <option value="all">Все статусы</option>
          <option value="active">🟢 Активные</option>
          <option value="completed">✅ Завершённые</option>
          <option value="error">❌ Ошибки</option>
        </select>

        <select
          value={agentFilter}
          onChange={(e) => setAgentFilter(e.target.value)}
          className="px-4 py-2 rounded-lg border border-nexus-200 bg-white"
        >
          <option value="all">Все агенты</option>
          <option value="codex">Codex</option>
          <option value="kimi">Kimi</option>
          <option value="gemini">Gemini</option>
          <option value="qwen">Qwen</option>
          <option value="claude">Claude</option>
          <option value="pi">Pi</option>
        </select>

        <button
          onClick={loadData}
          className="px-4 py-2 rounded-lg bg-nexus-100 hover:bg-nexus-200"
        >
          🔄 Обновить
        </button>
      </div>

      {/* Sessions Grid */}
      {loading ? (
        <div className="text-center py-12 text-nexus-400">
          ⏳ Загрузка...
        </div>
      ) : (
        <>
          {/* Active Sessions */}
          {activeSessions.length > 0 && (
            <section className="mb-8">
              <h2 className="text-lg font-semibold text-nexus-700 mb-4">
                🔴 Активные ({activeSessions.length})
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {activeSessions.map((session) => (
                  <SessionCard key={session.session_id} session={session} />
                ))}
              </div>
            </section>
          )}

          {/* Error Sessions */}
          {errorSessions.length > 0 && (
            <section className="mb-8">
              <h2 className="text-lg font-semibold text-red-600 mb-4">
                ❌ Ошибки ({errorSessions.length})
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {errorSessions.map((session) => (
                  <SessionCard key={session.session_id} session={session} />
                ))}
              </div>
            </section>
          )}

          {/* Completed Sessions */}
          {completedSessions.length > 0 && filter !== 'active' && (
            <section>
              <h2 className="text-lg font-semibold text-nexus-600 mb-4">
                ✅ Завершённые ({completedSessions.length})
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {completedSessions.slice(0, 20).map((session) => (
                  <SessionCard key={session.session_id} session={session} />
                ))}
              </div>
            </section>
          )}

          {/* Empty State */}
          {sessions.length === 0 && (
            <div className="text-center py-12 text-nexus-400">
              📭 Нет сессий
            </div>
          )}
        </>
      )}
    </main>
  );
}
