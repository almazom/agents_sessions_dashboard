'use client';

import { Session } from '@/lib/api';

interface Props {
  session: Session;
}

// Цвета агентов
const agentColors: Record<string, string> = {
  codex: 'bg-emerald-100 text-emerald-700 border-emerald-200',
  kimi: 'bg-amber-100 text-amber-700 border-amber-200',
  gemini: 'bg-blue-100 text-blue-700 border-blue-200',
  qwen: 'bg-violet-100 text-violet-700 border-violet-200',
  claude: 'bg-pink-100 text-pink-700 border-pink-200',
  pi: 'bg-cyan-100 text-cyan-700 border-cyan-200',
};

// Иконки статусов
const statusIcons: Record<string, string> = {
  active: '🟢',
  completed: '✅',
  error: '❌',
  paused: '⏸️',
  unknown: '⚪',
};

export default function SessionCard({ session }: Props) {
  const agentColor = agentColors[session.agent_type] || 'bg-gray-100 text-gray-700';
  const statusIcon = statusIcons[session.status] || '⚪';

  // Форматирование токенов
  const formatTokens = (n: number) => {
    if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
    if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
    return String(n);
  };

  // Сокращение пути
  const shortCwd = session.cwd.length > 40 
    ? `...${session.cwd.slice(-37)}` 
    : session.cwd;

  return (
    <div className="bg-white rounded-xl border border-nexus-200 p-4 shadow-sm hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <span className={`px-2 py-1 rounded-md text-xs font-medium border ${agentColor}`}>
          {session.agent_name}
        </span>
        <span className="text-sm">{statusIcon}</span>
      </div>

      {/* CWD */}
      <div className="text-xs text-nexus-400 font-mono mb-2" title={session.cwd}>
        📁 {shortCwd}
      </div>

      {/* Intent */}
      <p className="text-sm text-nexus-700 line-clamp-2 mb-3">
        {session.user_intent || 'Нет описания'}
      </p>

      {/* Tools */}
      {session.tool_calls.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-3">
          {session.tool_calls.slice(0, 4).map((tool, i) => (
            <span 
              key={i}
              className="px-2 py-0.5 bg-nexus-100 text-nexus-600 rounded text-xs"
            >
              {tool}
            </span>
          ))}
          {session.tool_calls.length > 4 && (
            <span className="text-xs text-nexus-400">
              +{session.tool_calls.length - 4}
            </span>
          )}
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between text-xs text-nexus-400 pt-2 border-t border-nexus-100">
        <span>
          🔤 {formatTokens(session.token_usage?.total_tokens || 0)}
        </span>
        <span>
          {session.timestamp_start 
            ? new Date(session.timestamp_start).toLocaleString('ru-RU', {
                day: 'numeric',
                month: 'short',
                hour: '2-digit',
                minute: '2-digit',
              })
            : '—'}
        </span>
      </div>

      {/* Error */}
      {session.error_message && (
        <div className="mt-2 p-2 bg-red-50 text-red-600 text-xs rounded">
          ⚠️ {session.error_message.slice(0, 100)}
        </div>
      )}
    </div>
  );
}
