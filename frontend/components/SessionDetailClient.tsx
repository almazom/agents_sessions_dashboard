'use client';

import Link from 'next/link';
import { useCallback, useEffect, useRef, useState } from 'react';

import AuthPanel from '@/components/AuthPanel';
import RichSessionCard from '@/components/RichSessionCard';
import { api, ApiError, SessionArtifactResponse, SessionStateModel } from '@/lib/api';

type AuthState = {
  authenticated: boolean;
  password_required: boolean;
  auth_required: boolean;
  password_enabled: boolean;
  telegram_enabled: boolean;
  telegram_configured: boolean;
  telegram_mode?: string | null;
  telegram_client_id?: string | null;
  telegram_bot_username?: string | null;
  telegram_widget_auth_url?: string | null;
  telegram_request_phone?: boolean;
};

type TelegramAuthResult = {
  id_token?: string;
  error?: string;
};

type TelegramLoginApi = {
  auth: (
    options: {
      client_id: number;
      request_access?: Array<'phone' | 'write'>;
    },
    callback: (result: TelegramAuthResult) => void,
  ) => void;
};

declare global {
  interface Window {
    Telegram?: {
      Login?: TelegramLoginApi;
    };
  }
}

function getApiErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof ApiError) {
    return error.detail || fallback;
  }
  return error instanceof Error ? error.message : fallback;
}

function formatTokens(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return String(n);
}

const timelineLabels: Record<string, string> = {
  user_message: 'Сообщение',
  tool_call: 'Инструмент',
  file_edit: 'Правка файла',
  plan_update: 'План',
  command: 'Команда',
  task_complete: 'Финиш',
  task_completed: 'Финиш',
  session_end: 'Завершение',
};

function formatTimelineLabel(eventType: string): string {
  if (timelineLabels[eventType]) {
    return timelineLabels[eventType];
  }

  const normalized = eventType.replace(/[_-]+/g, ' ').trim();
  return normalized ? normalized[0].toUpperCase() + normalized.slice(1) : 'Событие';
}

function formatTimelineTimestamp(value: string): string {
  if (!value) {
    return 'время не указано';
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat('ru-RU', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
}

const evidencePriorityItems = [
  {
    key: 'source-artifact',
    badge: 'highest trust',
    title: 'Source artifact',
    description: 'JSON или JSONL-файл остаётся главным источником правды по identity и time window.',
  },
  {
    key: 'artifact-timeline',
    badge: 'artifact timeline',
    title: 'Timeline from artifact',
    description: 'Хронология событий берётся из самой сессии и держит порядок шагов внутри окна.',
  },
  {
    key: 'repository-signals',
    badge: 'repo signal',
    title: 'Repository signals',
    description: 'Коммиты и файлы читаются только внутри окна этой сессии, а не как глобальная правда.',
  },
  {
    key: 'derived-layers',
    badge: 'derived layer',
    title: 'Intent and topics',
    description: 'Intent evolution и topic threads помогают понять смысл, но не переопределяют artifact.',
  },
] as const;

const stateLabelText: Record<string, string> = {
  archived: 'archived',
  restorable: 'restorable',
  live: 'live',
  queryable: 'queryable',
};

const stateLabelClasses: Record<string, string> = {
  archived: 'border-slate-200 bg-slate-100 text-slate-700',
  restorable: 'border-sky-200 bg-sky-50 text-sky-700',
  live: 'border-emerald-200 bg-emerald-50 text-emerald-700',
  queryable: 'border-amber-200 bg-amber-50 text-amber-700',
};

const safetyModeText: Record<string, string> = {
  'read-only': 'read-only',
  'ask-only': 'ask-only',
  'resume-allowed': 'resume-allowed',
};

const safetyModeClasses: Record<string, string> = {
  'read-only': 'border-slate-200 bg-slate-100 text-slate-700',
  'ask-only': 'border-blue-200 bg-blue-50 text-blue-700',
  'resume-allowed': 'border-emerald-200 bg-emerald-50 text-emerald-700',
};

function formatDetailedTimestamp(value: string): string {
  if (!value) {
    return 'время не указано';
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat('ru-RU', {
    year: 'numeric',
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
}

function formatSessionWindowValue(localValue?: string | null, isoValue?: string | null, fallback = '—'): string {
  if (localValue) {
    return localValue;
  }

  if (isoValue) {
    return formatDetailedTimestamp(isoValue);
  }

  return fallback;
}

interface Props {
  harness: string;
  artifactId: string;
}

export default function SessionDetailClient({ harness, artifactId }: Props) {
  const decodedHarness = decodeURIComponent(harness);
  const decodedArtifactId = decodeURIComponent(artifactId);
  const [detail, setDetail] = useState<SessionArtifactResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [authChecked, setAuthChecked] = useState(false);
  const [authenticated, setAuthenticated] = useState(false);
  const [authRequired, setAuthRequired] = useState(false);
  const [passwordRequired, setPasswordRequired] = useState(false);
  const [telegramEnabled, setTelegramEnabled] = useState(false);
  const [telegramConfigured, setTelegramConfigured] = useState(false);
  const [telegramMode, setTelegramMode] = useState<string | null>(null);
  const [telegramClientId, setTelegramClientId] = useState<string | null>(null);
  const [telegramBotUsername, setTelegramBotUsername] = useState<string | null>(null);
  const [telegramWidgetAuthUrl, setTelegramWidgetAuthUrl] = useState<string | null>(null);
  const [telegramRequestPhone, setTelegramRequestPhone] = useState(false);
  const [password, setPassword] = useState('');
  const [authSubmitting, setAuthSubmitting] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);
  const [authRevision, setAuthRevision] = useState(0);
  const telegramWidgetRef = useRef<HTMLDivElement | null>(null);

  const loadDetail = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const authStatus: AuthState = await api.getAuthStatus();
      setAuthChecked(true);
      setAuthRequired(authStatus.auth_required);
      setPasswordRequired(authStatus.password_enabled);
      setTelegramEnabled(authStatus.telegram_enabled);
      setTelegramConfigured(authStatus.telegram_configured);
      setTelegramMode(authStatus.telegram_mode ?? null);
      setTelegramClientId(authStatus.telegram_client_id ?? null);
      setTelegramBotUsername(authStatus.telegram_bot_username ?? null);
      setTelegramWidgetAuthUrl(authStatus.telegram_widget_auth_url ?? null);
      setTelegramRequestPhone(Boolean(authStatus.telegram_request_phone));
      setAuthenticated(authStatus.authenticated || !authStatus.auth_required);

      if (authStatus.auth_required && !authStatus.authenticated) {
        setDetail(null);
        setLoading(false);
        return;
      }

      const payload = await api.getSessionArtifact(decodedHarness, decodedArtifactId);
      setDetail(payload);
    } catch (loadError) {
      if (loadError instanceof ApiError && loadError.status === 401) {
        setAuthenticated(false);
        setAuthRequired(true);
        setDetail(null);
        setAuthError('Сессия истекла. Войдите снова.');
      } else {
        setError(getApiErrorMessage(loadError, 'Не удалось загрузить страницу сессии.'));
      }
    } finally {
      setLoading(false);
    }
  }, [decodedArtifactId, decodedHarness]);

  useEffect(() => {
    void loadDetail();
  }, [authRevision, loadDetail]);

  useEffect(() => {
    const container = telegramWidgetRef.current;
    if (!container) {
      return;
    }

    container.innerHTML = '';

    if (!authChecked || authenticated || telegramMode !== 'widget' || !telegramEnabled || !telegramBotUsername || !telegramWidgetAuthUrl) {
      return;
    }

    const script = document.createElement('script');
    script.async = true;
    script.src = 'https://telegram.org/js/telegram-widget.js?22';
    script.setAttribute('data-telegram-login', telegramBotUsername);
    script.setAttribute('data-size', 'large');
    script.setAttribute('data-radius', '999');
    script.setAttribute('data-userpic', 'false');
    script.setAttribute('data-auth-url', telegramWidgetAuthUrl);
    container.appendChild(script);

    return () => {
      container.innerHTML = '';
    };
  }, [authChecked, authenticated, telegramBotUsername, telegramEnabled, telegramMode, telegramWidgetAuthUrl]);

  const handleLogin = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setAuthSubmitting(true);
    setAuthError(null);

    try {
      await api.login(password);
      setPassword('');
      setAuthRevision((value) => value + 1);
    } catch (loginError) {
      if (loginError instanceof ApiError && loginError.status === 401) {
        setAuthError('Неверный пароль.');
      } else {
        setAuthError('Не удалось войти прямо сейчас.');
      }
    } finally {
      setAuthSubmitting(false);
    }
  };

  const completeTelegramLogin = async (idToken: string) => {
    try {
      await api.loginWithTelegram(idToken);
      setPassword('');
      setAuthError(null);
      setAuthRevision((value) => value + 1);
    } catch (loginError) {
      if (loginError instanceof ApiError && loginError.status === 403) {
        setAuthError('Этот Telegram аккаунт не разрешён.');
      } else {
        setAuthError('Не удалось войти через Telegram.');
      }
    } finally {
      setAuthSubmitting(false);
    }
  };

  const handleTelegramLogin = () => {
    setAuthSubmitting(true);
    setAuthError(null);

    if (!telegramEnabled) {
      setAuthSubmitting(false);
      setAuthError('Telegram login is not configured on the server yet.');
      return;
    }

    const telegramLogin = window.Telegram?.Login;
    const numericClientId = Number(telegramClientId);

    if (!telegramLogin?.auth || !telegramClientId || Number.isNaN(numericClientId)) {
      window.location.assign('/api/auth/telegram/start');
      return;
    }

    telegramLogin.auth(
      {
        client_id: numericClientId,
        request_access: telegramRequestPhone ? ['phone'] : [],
      },
      (result) => {
        if (result.error) {
          setAuthSubmitting(false);
          setAuthError(
            result.error === 'access_denied'
              ? 'Telegram login was cancelled.'
              : 'Telegram login failed.',
          );
          return;
        }

        if (!result.id_token) {
          setAuthSubmitting(false);
          setAuthError('Telegram did not return an ID token.');
          return;
        }

        void completeTelegramLogin(result.id_token);
      },
    );
  };

  const handleLogout = async () => {
    try {
      await api.logout();
    } finally {
      setAuthenticated(false);
      setDetail(null);
      setError(null);
      setPassword('');
      setAuthError(null);
      setAuthRevision((value) => value + 1);
    }
  };

  if (authChecked && !authenticated) {
    return (
      <main className="min-h-screen p-6">
        <header className="mb-8 flex items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-nexus-800">🗂 Session Detail</h1>
            <p className="mt-1 text-nexus-500">{decodedHarness} / {decodedArtifactId}</p>
          </div>
          <Link href="/" className="rounded-lg border border-nexus-200 bg-white px-4 py-2 text-sm text-nexus-700 hover:bg-nexus-50">
            ← На главную
          </Link>
        </header>

        <AuthPanel
          passwordRequired={passwordRequired}
          telegramEnabled={telegramEnabled}
          telegramConfigured={telegramConfigured}
          telegramMode={telegramMode}
          authSubmitting={authSubmitting}
          authError={authError}
          password={password}
          telegramWidgetRef={telegramWidgetRef}
          onPasswordChange={setPassword}
          onPasswordSubmit={handleLogin}
          onTelegramLogin={handleTelegramLogin}
        />
      </main>
    );
  }

  const session = detail?.session;
  const messageAnchors = session?.message_anchors ?? {
    first: session?.first_user_message || '',
    middle: [],
    last: session?.last_user_message || '',
  };
  const middleAnchors = messageAnchors.middle || [];
  const timelineEvents = session?.timeline || [];
  const visibleUserTurns = session?.user_messages?.length || session?.user_message_count || 0;
  const gitCommits = session?.git_commits || [];
  const gitRepositoryRoot = session?.git_repository_root || null;
  const topicThreads = session?.topic_threads || [];
  const timeWindow = session?.time_window;
  const defaultStateModel: SessionStateModel = {
    labels: session?.activity_state === 'live' ? ['live'] : ['archived'],
    safety_mode: 'read-only',
    summary: 'Сейчас detail page работает как безопасное досье: только чтение и честные placeholders.',
    rationale: [
      'Ask и resume ещё не подключены к реальному runtime flow.',
      'UI не обещает действий, которые могут скрыто менять source artifact.',
    ],
    capabilities: {
      can_ask: false,
      can_resume: false,
      can_restore: false,
    },
  };
  const stateModel = session?.state_model ?? defaultStateModel;
  const safetyMode = stateModel.safety_mode || 'read-only';
  const stateLabels = stateModel.labels?.length > 0 ? stateModel.labels : defaultStateModel.labels;
  const capabilities = stateModel.capabilities ?? defaultStateModel.capabilities!;
  const askCapability = stateModel.ask_session ?? {
    available: capabilities.can_ask,
    label: capabilities.can_ask ? 'Query layer доступен' : 'Пока не подключено',
    detail: capabilities.can_ask
      ? 'Безопасный ask-only режим уже можно показывать без обещания resume.'
      : 'Будущий ask-only слой останется недеструктивным и будет работать поверх artifact.',
  };
  const resumeCapability = stateModel.resume_session ?? {
    available: capabilities.can_resume,
    label: capabilities.can_resume ? 'Resume поддержан' : 'Пока не разрешено',
    detail: capabilities.can_resume
      ? 'Resume-allowed включается только когда backend явно разрешает продолжение.'
      : 'Resume появится только после явных harness-specific safety checks.',
  };
  const timeWindowStartValue = formatSessionWindowValue(
    timeWindow?.started_at_local || session?.started_at_local,
    timeWindow?.started_at || session?.started_at,
  );
  const timeWindowEndValue = formatSessionWindowValue(
    timeWindow?.ended_at_local || session?.ended_at_local,
    timeWindow?.ended_at || session?.ended_at,
  );
  const timeWindowDurationValue = timeWindow?.duration_human || session?.duration_human || '—';
  const timeWindowScope = [
    `${timelineEvents.length} timeline events`,
    `${(session?.files_modified || []).length} file signals`,
    `${gitCommits.length} commit signals`,
  ].join(' · ');

  return (
    <main data-testid="session-detail-page" className="min-h-screen p-6">
      <header className="mb-8 flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <div className="font-mono text-[11px] uppercase tracking-[0.24em] text-nexus-500">
            session detail
          </div>
          <h1 className="mt-2 text-3xl font-bold text-nexus-800">
            Отдельная страница сессии
          </h1>
          <p className="mt-1 text-nexus-500">
            {decodedHarness} / {decodedArtifactId}
          </p>
        </div>

        <div className="flex gap-3">
          <Link href="/" className="rounded-lg border border-nexus-200 bg-white px-4 py-2 text-sm text-nexus-700 hover:bg-nexus-50">
            ← На главную
          </Link>
          {authRequired && authenticated && (
            <button
              data-testid="logout-button"
              onClick={handleLogout}
              className="rounded-lg border border-nexus-200 bg-white px-4 py-2 text-sm text-nexus-700 hover:bg-nexus-50"
            >
              Выйти
            </button>
          )}
        </div>
      </header>

      {loading ? (
        <div className="animate-pulse rounded-[28px] border border-nexus-200 bg-white p-6 shadow-sm">
          <div className="h-5 w-40 rounded bg-nexus-200" />
          <div className="mt-3 h-9 w-72 rounded bg-nexus-100" />
          <div className="mt-6 grid gap-3 lg:grid-cols-2">
            <div className="h-24 rounded-2xl bg-nexus-100" />
            <div className="h-24 rounded-2xl bg-nexus-100" />
          </div>
        </div>
      ) : error ? (
        <div className="rounded-[28px] border border-red-200 bg-red-50 px-6 py-5 text-sm text-red-700">
          ⚠️ {error}
        </div>
      ) : session ? (
        <>
          <RichSessionCard
            session={session}
            dataTestId="session-detail-card"
            eyebrow="🧭 Session Detail"
            title={session.agent_name || 'Сессия'}
            description={`Открыт отдельный landing для одного session artifact. Таймзона: ${detail?.meta.timezone}.`}
            topBadgeText={`detail :: ${session.route?.harness || decodedHarness}/${session.route?.id || decodedArtifactId}`}
            detailRows={[
              { label: 'Путь к файлу', value: session.path, emoji: '📁' },
              { label: 'Рабочая директория', value: session.cwd || '—', emoji: '📁' },
            ]}
            showMessageExtremes={false}
            intentBadgeText="derived layer"
          />

          <section className="grid gap-4 xl:grid-cols-[minmax(0,1.15fr)_minmax(0,0.85fr)]">
            <article
              data-testid="time-window-block"
              className="rounded-[28px] border border-[#d7e0ea] bg-[linear-gradient(135deg,#f4fbff_0%,#ffffff_48%,#fffef6_100%)] p-5 shadow-sm"
            >
              <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="font-mono text-[11px] uppercase tracking-[0.24em] text-nexus-500">
                    time window
                  </div>
                  <h2 className="mt-2 text-2xl font-semibold text-nexus-900">
                    Временное окно сессии
                  </h2>
                  <p className="mt-1 max-w-3xl text-sm leading-6 text-nexus-600">
                    Коммиты, файлы и timeline ниже читаются только внутри этого окна, а не как отдельная глобальная история.
                  </p>
                </div>
                <span className="rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-emerald-700">
                  source artifact
                </span>
              </div>

              <div className="grid gap-3 md:grid-cols-2">
                <div
                  data-testid="time-window-start"
                  className="rounded-[22px] border border-nexus-200 bg-white/90 p-4"
                >
                  <div className="text-[11px] font-semibold uppercase tracking-[0.16em] text-nexus-500">
                    Начало
                  </div>
                  <div className="mt-2 text-base font-semibold text-nexus-900">
                    {timeWindowStartValue}
                  </div>
                  <div className="mt-1 text-xs text-nexus-500">
                    source timestamp
                  </div>
                </div>

                <div
                  data-testid="time-window-end"
                  className="rounded-[22px] border border-nexus-200 bg-white/90 p-4"
                >
                  <div className="text-[11px] font-semibold uppercase tracking-[0.16em] text-nexus-500">
                    Конец
                  </div>
                  <div className="mt-2 text-base font-semibold text-nexus-900">
                    {timeWindowEndValue}
                  </div>
                  <div className="mt-1 text-xs text-nexus-500">
                    explicit window end
                  </div>
                </div>

                <div
                  data-testid="time-window-duration"
                  className="rounded-[22px] border border-nexus-200 bg-white/90 p-4"
                >
                  <div className="text-[11px] font-semibold uppercase tracking-[0.16em] text-nexus-500">
                    Длительность
                  </div>
                  <div className="mt-2 text-base font-semibold text-nexus-900">
                    {timeWindowDurationValue}
                  </div>
                  <div className="mt-1 text-xs text-nexus-500">
                    окно досье, а не только latest snapshot
                  </div>
                </div>

                <div
                  data-testid="time-window-scope"
                  className="rounded-[22px] border border-nexus-200 bg-white/90 p-4"
                >
                  <div className="text-[11px] font-semibold uppercase tracking-[0.16em] text-nexus-500">
                    Что привязано к окну
                  </div>
                  <div className="mt-2 text-sm leading-6 text-nexus-800">
                    Коммиты, files modified и timeline ниже читаются только внутри этого окна сессии.
                  </div>
                  <div className="mt-1 text-xs text-nexus-500">
                    {timeWindowScope}
                  </div>
                </div>
              </div>
            </article>

            <article
              data-testid="evidence-priority"
              className="rounded-[28px] border border-[#d7e0ea] bg-white p-5 shadow-sm"
            >
              <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="font-mono text-[11px] uppercase tracking-[0.24em] text-nexus-500">
                    evidence priority
                  </div>
                  <h2 className="mt-2 text-2xl font-semibold text-nexus-900">
                    Иерархия доверия
                  </h2>
                  <p className="mt-1 text-sm leading-6 text-nexus-600">
                    Если intent layer и git narrative расходятся, page сохраняет оба сигнала и не прячет расхождение.
                  </p>
                </div>
                <span className="rounded-full border border-amber-200 bg-amber-50 px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-amber-700">
                  trust map
                </span>
              </div>

              <div className="grid gap-3">
                {evidencePriorityItems.map((item, index) => (
                  <div
                    key={item.key}
                    data-testid={`evidence-priority-item-${index}`}
                    className="rounded-[22px] border border-nexus-200 bg-[#fbfdff] p-4"
                  >
                    <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
                      <div className="text-sm font-semibold text-nexus-900">
                        {index + 1}. {item.title}
                      </div>
                      <span className="rounded-full border border-nexus-200 bg-white px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-nexus-600">
                        {item.badge}
                      </span>
                    </div>
                    <div className="text-sm leading-6 text-nexus-700">
                      {item.description}
                    </div>
                  </div>
                ))}
              </div>
            </article>
          </section>

          <section
            data-testid="message-anchors"
            className="rounded-[28px] border border-[#d7e0ea] bg-[linear-gradient(135deg,#fffdf3_0%,#ffffff_48%,#edf7ff_100%)] p-5 shadow-sm"
          >
            <div className="mb-4 flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <div className="font-mono text-[11px] uppercase tracking-[0.24em] text-nexus-500">
                    message anchors
                  </div>
                  <span className="rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-emerald-700">
                    source artifact
                  </span>
                </div>
                <h2 className="mt-2 text-2xl font-semibold text-nexus-900">
                  Опорные сообщения сессии
                </h2>
                <p className="mt-1 max-w-3xl text-sm leading-6 text-nexus-600">
                  Старт, ключевые повороты и финал разговора. Здесь лучше держать живые формулировки пользователя, а не только сжатый summary.
                </p>
              </div>
              <div className="rounded-full border border-nexus-200 bg-white px-3 py-1 text-xs font-medium text-nexus-600">
                {visibleUserTurns} user turns
              </div>
            </div>

            <div className="grid gap-4 xl:grid-cols-[minmax(0,0.9fr)_minmax(0,1.2fr)_minmax(0,0.9fr)]">
              <div className="rounded-[24px] border border-[#d7e0ea] bg-white/90 p-4">
                <div className="mb-3 text-[11px] font-semibold uppercase tracking-[0.16em] text-nexus-500">
                  01 Старт
                </div>
                <div
                  data-testid="message-anchor-first"
                  className="rounded-2xl border border-nexus-200 bg-[#fbfdff] p-4 text-sm leading-7 text-nexus-800 whitespace-pre-wrap break-words"
                >
                  {messageAnchors.first || session.first_user_message || 'Стартовое сообщение не найдено.'}
                </div>
              </div>

              <div className="rounded-[24px] border border-[#d7e0ea] bg-white/95 p-4">
                <div className="mb-3 flex items-center justify-between gap-3">
                  <div className="text-[11px] font-semibold uppercase tracking-[0.16em] text-nexus-500">
                    02 Поворотные сообщения
                  </div>
                  <div className="text-xs text-nexus-500">
                    2-4 опорные реплики из середины
                  </div>
                </div>
                <div className="grid gap-3">
                  {middleAnchors.length > 0 ? middleAnchors.map((message, index) => (
                    <div
                      key={`${index + 1}-${message}`}
                      data-testid={`message-anchor-middle-${index}`}
                      className="rounded-2xl border border-nexus-200 bg-[#fbfdff] px-4 py-3"
                    >
                      <div className="mb-1 text-[11px] font-semibold uppercase tracking-[0.16em] text-nexus-500">
                        Поворот {index + 1}
                      </div>
                      <div className="text-sm leading-7 text-nexus-800 whitespace-pre-wrap break-words">
                        {message}
                      </div>
                    </div>
                  )) : (
                    <div className="rounded-2xl border border-dashed border-nexus-200 bg-[#fbfdff] px-4 py-6 text-sm text-nexus-500">
                      Пока не хватает срединных сообщений, чтобы выделить отдельные поворотные точки.
                    </div>
                  )}
                </div>
              </div>

              <div className="rounded-[24px] border border-[#d7e0ea] bg-white/90 p-4">
                <div className="mb-3 text-[11px] font-semibold uppercase tracking-[0.16em] text-nexus-500">
                  03 Финиш
                </div>
                <div
                  data-testid="message-anchor-last"
                  className="rounded-2xl border border-nexus-200 bg-[#fbfdff] p-4 text-sm leading-7 text-nexus-800 whitespace-pre-wrap break-words"
                >
                  {messageAnchors.last || session.last_user_message || 'Финальное сообщение не найдено.'}
                </div>
              </div>
            </div>
          </section>

          <section className="grid gap-4 lg:grid-cols-2">
            <div className="rounded-[24px] border border-[#d7e0ea] bg-white p-5 shadow-sm">
              <div className="mb-3 font-mono text-[11px] uppercase tracking-[0.24em] text-nexus-500">
                execution context
              </div>
              <div className="grid gap-3 text-sm text-nexus-700">
                <div className="rounded-2xl border border-nexus-200 bg-nexus-50 px-4 py-3">
                  Internal session id: <span className="font-mono">{session.session_id}</span>
                </div>
                <div className="rounded-2xl border border-nexus-200 bg-nexus-50 px-4 py-3">
                  Branch: <span className="font-mono">{session.git_branch || '—'}</span>
                </div>
                <div className="rounded-2xl border border-nexus-200 bg-nexus-50 px-4 py-3">
                  Repo: <span className="font-mono break-all">{gitRepositoryRoot || '—'}</span>
                </div>
                <div className="rounded-2xl border border-nexus-200 bg-nexus-50 px-4 py-3">
                  Tokens: <span className="font-semibold">{formatTokens(session.token_usage?.total_tokens || 0)}</span>
                </div>
              </div>
            </div>

            <div className="rounded-[24px] border border-[#d7e0ea] bg-white p-5 shadow-sm">
              <div className="mb-3 font-mono text-[11px] uppercase tracking-[0.24em] text-nexus-500">
                execution footprint
              </div>
              <div className="grid gap-3">
                <div className="rounded-2xl border border-nexus-200 bg-[#fbfdff] p-4">
                  <div className="mb-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-nexus-500">
                    🛠 Инструменты
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {(session.tool_calls || []).length > 0 ? session.tool_calls.map((tool) => (
                      <span key={tool} className="rounded-full border border-nexus-200 bg-nexus-50 px-2.5 py-1 text-xs text-nexus-600">
                        {tool}
                      </span>
                    )) : (
                      <span className="text-sm text-nexus-500">Инструменты не зафиксированы.</span>
                    )}
                  </div>
                </div>

                <div className="rounded-2xl border border-nexus-200 bg-[#fbfdff] p-4">
                  <div className="mb-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-nexus-500">
                    📝 Изменённые файлы
                  </div>
                  <div className="grid gap-2">
                    {(session.files_modified || []).length > 0 ? session.files_modified.slice(0, 8).map((filePath) => (
                      <div key={filePath} className="font-mono text-[13px] text-nexus-700 break-all">
                        {filePath}
                      </div>
                    )) : (
                      <span className="text-sm text-nexus-500">Изменения файлов не зафиксированы.</span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </section>

          <section
            data-testid="git-commits-block"
            className="rounded-[28px] border border-[#d7e0ea] bg-[linear-gradient(135deg,#f5fff7_0%,#ffffff_42%,#f7fbff_100%)] p-5 shadow-sm"
          >
            <div className="mb-5 flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <div className="font-mono text-[11px] uppercase tracking-[0.24em] text-nexus-500">
                    git commits during session
                  </div>
                  <span className="rounded-full border border-blue-200 bg-blue-50 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-blue-700">
                    repo signal
                  </span>
                </div>
                <h2 className="mt-2 text-2xl font-semibold text-nexus-900">
                  Коммиты в окно этой сессии
                </h2>
                <p className="mt-1 max-w-3xl text-sm leading-6 text-nexus-600">
                  Это дополнительный источник смысла: заголовки коммитов помогают увидеть, чем разговор закончился в репозитории, а не только в чате.
                </p>
              </div>
              <div className="flex flex-wrap gap-2">
                <span className="rounded-full border border-nexus-200 bg-white px-3 py-1 text-xs font-medium text-nexus-600">
                  {gitCommits.length} commits
                </span>
                <span className="rounded-full border border-nexus-200 bg-nexus-50 px-3 py-1 text-xs font-medium text-nexus-600">
                  {gitRepositoryRoot ? 'repo linked' : 'repo unavailable'}
                </span>
              </div>
            </div>

            {gitRepositoryRoot ? (
              <div className="mb-4 rounded-2xl border border-nexus-200 bg-white/80 px-4 py-3 text-sm text-nexus-700">
                Repository root: <span className="font-mono break-all text-nexus-800">{gitRepositoryRoot}</span>
              </div>
            ) : null}

            {gitCommits.length > 0 ? (
              <div className="grid gap-3">
                {gitCommits.map((commit, index) => (
                  <article
                    key={`${commit.hash}-${index}`}
                    data-testid={`git-commit-item-${index}`}
                    className="rounded-[24px] border border-[#d7e0ea] bg-white/90 p-4"
                  >
                    <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                      <div>
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-1 font-mono text-xs text-emerald-700">
                            {commit.short_hash}
                          </span>
                          <span className="text-xs text-nexus-500">
                            {commit.author_name}
                          </span>
                        </div>
                        <h3 className="mt-3 text-base font-semibold text-nexus-900">
                          {commit.title}
                        </h3>
                      </div>
                      <div className="rounded-full border border-nexus-200 bg-[#fbfdff] px-3 py-1 text-xs text-nexus-500">
                        {commit.committed_at_local || formatTimelineTimestamp(commit.committed_at)}
                      </div>
                    </div>
                  </article>
                ))}
              </div>
            ) : (
              <div className="rounded-[24px] border border-dashed border-nexus-200 bg-white/80 px-4 py-8 text-sm text-nexus-500">
                {gitRepositoryRoot
                  ? 'Коммитов в границах этой сессии не найдено.'
                  : 'Рабочая директория сессии не связана с git-репозиторием, поэтому commit history здесь недоступен.'}
              </div>
            )}
          </section>

          <section
            data-testid="session-timeline"
            className="rounded-[28px] border border-[#d7e0ea] bg-white p-5 shadow-sm"
          >
            <div className="mb-5 flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <div className="font-mono text-[11px] uppercase tracking-[0.24em] text-nexus-500">
                    session timeline
                  </div>
                  <span className="rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-emerald-700">
                    artifact timeline
                  </span>
                </div>
                <h2 className="mt-2 text-2xl font-semibold text-nexus-900">
                  Хронология ключевых событий
                </h2>
                <p className="mt-1 max-w-3xl text-sm leading-6 text-nexus-600">
                  Не только summary, а последовательность шагов: что пользователь попросил, какой инструмент запускался и где пошла правка.
                </p>
              </div>
              <div className="rounded-full border border-nexus-200 bg-nexus-50 px-3 py-1 text-xs font-medium text-nexus-600">
                {timelineEvents.length} events
              </div>
            </div>

            {timelineEvents.length > 0 ? (
              <div className="relative pl-7">
                <div className="absolute left-[13px] top-1 bottom-1 w-px bg-[linear-gradient(180deg,#dbeafe_0%,#f59e0b_100%)]" />
                <div className="grid gap-4">
                  {timelineEvents.map((event, index) => (
                    <div
                      key={`${event.timestamp}-${event.event_type}-${index}`}
                      data-testid={`session-timeline-item-${index}`}
                      className="relative"
                    >
                      <div className="absolute -left-7 top-4 flex h-7 w-7 items-center justify-center rounded-full border border-[#d7e0ea] bg-white text-sm shadow-sm">
                        {event.icon || '📝'}
                      </div>
                      <div className="rounded-[22px] border border-[#d7e0ea] bg-[linear-gradient(135deg,#fbfdff_0%,#ffffff_100%)] p-4">
                        <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                          <div className="text-sm font-semibold text-nexus-900">
                            {event.description}
                          </div>
                          <div className="flex flex-wrap gap-2 text-xs">
                            <span className="rounded-full border border-nexus-200 bg-nexus-50 px-2.5 py-1 text-nexus-600">
                              {formatTimelineLabel(event.event_type)}
                            </span>
                            <span className="rounded-full border border-nexus-200 bg-white px-2.5 py-1 text-nexus-500">
                              {formatTimelineTimestamp(event.timestamp)}
                            </span>
                          </div>
                        </div>
                        {event.details && (
                          <div className="mt-3 rounded-2xl border border-nexus-200 bg-nexus-50 px-4 py-3 text-sm leading-6 text-nexus-700 whitespace-pre-wrap break-words">
                            {event.details}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="rounded-[24px] border border-dashed border-nexus-200 bg-[#fbfdff] px-4 py-8 text-sm text-nexus-500">
                Таймлайн ещё не собран для этой сессии.
              </div>
            )}
          </section>

          <section className="grid gap-4 xl:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
            <article
              data-testid="topic-threads"
              className="rounded-[28px] border border-[#d7e0ea] bg-[linear-gradient(135deg,#fff8e9_0%,#ffffff_48%,#f8fbff_100%)] p-5 shadow-sm"
            >
              <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="font-mono text-[11px] uppercase tracking-[0.24em] text-nexus-500">
                    topic threads
                  </div>
                  <h2 className="mt-2 text-2xl font-semibold text-nexus-900">
                    Тематические потоки
                  </h2>
                  <p className="mt-1 text-sm leading-6 text-nexus-600">
                    Это отдельный semantic layer: не куда пользователь вёл сессию, а о каких предметных блоках реально шёл разговор.
                  </p>
                </div>
                <span className="rounded-full border border-amber-200 bg-amber-50 px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-amber-700">
                  derived layer
                </span>
              </div>

              {topicThreads.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {topicThreads.map((topic, index) => (
                    <span
                      key={`${topic}-${index}`}
                      data-testid={`topic-thread-${index}`}
                      className="rounded-full border border-[#d7e0ea] bg-white px-3 py-1.5 text-sm text-nexus-700"
                    >
                      {topic}
                    </span>
                  ))}
                </div>
              ) : (
                <div className="rounded-[22px] border border-dashed border-nexus-200 bg-white/90 px-4 py-6 text-sm text-nexus-500">
                  Topic threads ещё не извлечены. Здесь должен жить отдельный слой тем, а не дубли intent bullets.
                </div>
              )}
            </article>

            <article
              data-testid="future-actions"
              className="rounded-[28px] border border-[#d7e0ea] bg-white p-5 shadow-sm"
            >
              <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="font-mono text-[11px] uppercase tracking-[0.24em] text-nexus-500">
                    future actions
                  </div>
                  <h2 className="mt-2 text-2xl font-semibold text-nexus-900">
                    Будущие действия
                  </h2>
                  <p className="mt-1 text-sm leading-6 text-nexus-600">
                    Это безопасные placeholders. Они показывают roadmap detail page, но не запускают скрытые runtime-действия.
                  </p>
                </div>
                <span className={`rounded-full border px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] ${safetyModeClasses[safetyMode] || safetyModeClasses['read-only']}`}>
                  {safetyModeText[safetyMode] || safetyMode}
                </span>
              </div>

              <div
                data-testid="session-state-model"
                className="mb-4 rounded-[22px] border border-nexus-200 bg-[#fbfdff] p-4"
              >
                <div className="mb-3 flex flex-wrap items-center gap-2">
                  {stateLabels.map((label, index) => (
                    <span
                      key={`${label}-${index}`}
                      data-testid={`state-label-${index}`}
                      className={`rounded-full border px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] ${stateLabelClasses[label] || stateLabelClasses.archived}`}
                    >
                      {stateLabelText[label] || label}
                    </span>
                  ))}
                  <span className={`rounded-full border px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] ${safetyModeClasses[safetyMode] || safetyModeClasses['read-only']}`}>
                    {safetyModeText[safetyMode] || safetyMode}
                  </span>
                </div>
                <div className="text-sm leading-6 text-nexus-800">
                  {stateModel.summary}
                </div>
                <div className="mt-3 grid gap-2">
                  {stateModel.rationale.map((reason, index) => (
                    <div
                      key={`${index + 1}-${reason}`}
                      data-testid={`state-rationale-${index}`}
                      className="rounded-2xl border border-nexus-200 bg-white px-3 py-2 text-sm text-nexus-700"
                    >
                      {reason}
                    </div>
                  ))}
                </div>
              </div>

              <div className="grid gap-3 md:grid-cols-2">
                <article
                  data-testid="future-action-ask"
                  className="rounded-[22px] border border-[#d7e0ea] bg-[linear-gradient(135deg,#fffaf0_0%,#ffffff_100%)] p-4"
                >
                  <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                    <h3 className="text-base font-semibold text-nexus-900">
                      Ask This Session
                    </h3>
                    <span className="rounded-full border border-amber-200 bg-amber-50 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-amber-700">
                      placeholder
                    </span>
                  </div>
                  <div className="text-sm leading-6 text-nexus-700">
                    Вопросы к artifact будут идти поверх JSON и timeline без изменения исходного файла.
                  </div>
                  <div className="mt-3 rounded-2xl border border-nexus-200 bg-white px-3 py-3 text-sm text-nexus-800">
                    <div className="font-semibold">{askCapability.label}</div>
                    <div className="mt-1 text-nexus-600">{askCapability.detail}</div>
                  </div>
                </article>

                <article
                  data-testid="future-action-resume"
                  className="rounded-[22px] border border-[#d7e0ea] bg-[linear-gradient(135deg,#f5f9ff_0%,#ffffff_100%)] p-4"
                >
                  <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                    <h3 className="text-base font-semibold text-nexus-900">
                      Continue / Resume Session
                    </h3>
                    <span className="rounded-full border border-slate-200 bg-slate-100 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-700">
                      safety gated
                    </span>
                  </div>
                  <div className="text-sm leading-6 text-nexus-700">
                    Продолжение появится только когда harness-specific flow научится явно проверять безопасность и capability.
                  </div>
                  <div className="mt-3 rounded-2xl border border-nexus-200 bg-white px-3 py-3 text-sm text-nexus-800">
                    <div className="font-semibold">{resumeCapability.label}</div>
                    <div className="mt-1 text-nexus-600">{resumeCapability.detail}</div>
                  </div>
                </article>
              </div>
            </article>
          </section>
        </>
      ) : (
        <div className="rounded-[28px] border border-nexus-200 bg-white px-6 py-5 text-sm text-nexus-500 shadow-sm">
          📭 Сессия не найдена.
        </div>
      )}
    </main>
  );
}
