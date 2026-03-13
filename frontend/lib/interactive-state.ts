import type { InteractiveBootPayload } from '@/lib/api';

export type InteractiveRoutePhase = 'ready' | 'blocked';

export interface InteractiveTimelineEntry {
  id: string;
  summary: string;
  detail: string;
}

export interface InteractiveComposerState {
  enabled: boolean;
  placeholder: string;
  helperText: string;
  submitLabel: string;
}

export interface InteractiveRouteState {
  phase: InteractiveRoutePhase;
  statusLabel: string;
  timelineEntries: InteractiveTimelineEntry[];
  composer: InteractiveComposerState;
}

function summarizeEntry(item: Record<string, unknown>, fallbackId: string): InteractiveTimelineEntry {
  const summary =
    typeof item.summary === 'string'
      ? item.summary
      : typeof item.title === 'string'
        ? item.title
        : typeof item.text === 'string'
          ? item.text
          : 'Interactive event';
  const detail =
    typeof item.detail === 'string'
      ? item.detail
      : typeof item.description === 'string'
        ? item.description
        : 'No extra detail was captured for this event yet.';

  return {
    id: typeof item.id === 'string' ? item.id : fallbackId,
    summary,
    detail,
  };
}

function buildTimelineEntries(payload: InteractiveBootPayload): InteractiveTimelineEntry[] {
  const timelineSource = [...payload.tail.items, ...payload.replay.items];
  const mappedEntries = timelineSource.map((item, index) =>
    summarizeEntry(item, `interactive-entry-${index + 1}`),
  );

  if (mappedEntries.length > 0) {
    return mappedEntries;
  }

  return [
    {
      id: 'interactive-entry-placeholder',
      summary: 'Waiting for replay and live timeline data',
      detail: 'This route now has a frontend state model, but the replay/live transport cards have not been delivered yet.',
    },
  ];
}

export function buildInteractiveRouteState(payload: InteractiveBootPayload): InteractiveRouteState {
  const phase: InteractiveRoutePhase = payload.interactive_session.available ? 'ready' : 'blocked';

  if (phase === 'blocked') {
    return {
      phase,
      statusLabel: payload.interactive_session.label,
      timelineEntries: buildTimelineEntries(payload),
      composer: {
        enabled: false,
        placeholder: 'Interactive continuation is blocked for this session.',
        helperText: payload.interactive_session.detail,
        submitLabel: 'Continue session',
      },
    };
  }

  return {
    phase,
    statusLabel: 'Live timeline ready',
    timelineEntries: buildTimelineEntries(payload),
    composer: {
      enabled: true,
      placeholder: 'Send the next prompt to continue this session.',
      helperText: 'Composer state is ready. Prompt submit wiring lands in the next transport/integration cards.',
      submitLabel: 'Queue prompt',
    },
  };
}
