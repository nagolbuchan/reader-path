import React from 'react';
import { crewApi, type CoursePreviewData, type CrewRunLog } from '../lib/api';
import { TOPIC_CATEGORY_LABELS } from '../lib/api';

interface CoursePreviewProps {
  previewData: CoursePreviewData;
  jobId?: string | null;
  onConfirm?: () => void | Promise<void>;
  onRegenerate?: () => void;
  isSaving?: boolean;
}

export const CoursePreview: React.FC<CoursePreviewProps> = ({
  previewData,
  jobId = null,
  onConfirm,
  onRegenerate,
  isSaving = false,
}) => {
  const [activeModuleIndex, setActiveModuleIndex] = React.useState(0);
  const [saving, setSaving] = React.useState(false);
  const [showLog, setShowLog] = React.useState(false);
  const [logLoading, setLogLoading] = React.useState(false);
  const [logError, setLogError] = React.useState<string | null>(null);
  const [runLog, setRunLog] = React.useState<CrewRunLog | null>(null);
  const [logTab, setLogTab] = React.useState<'final' | 'agents' | 'verbose'>(
    'final'
  );

  const handleConfirm = async () => {
    if (!onConfirm) return;
    setSaving(true);
    try {
      await onConfirm();
    } finally {
      setSaving(false);
    }
  };

  const handleOpenLog = async () => {
    if (!jobId) return;
    setShowLog(true);
    if (runLog) return;
    setLogLoading(true);
    setLogError(null);
    try {
      const log = await crewApi.getJobLog(jobId);
      setRunLog(log);
    } catch (err) {
      setLogError(
        err instanceof Error ? err.message : 'Could not load agent log.'
      );
    } finally {
      setLogLoading(false);
    }
  };

  const handleCopyLog = async () => {
    if (!runLog) return;
    await navigator.clipboard.writeText(JSON.stringify(runLog, null, 2));
  };

  const busy = isSaving || saving;
  const currentModule = previewData.modules[activeModuleIndex];

  const logBody = (() => {
    if (!runLog) return '';
    if (logTab === 'final') {
      return JSON.stringify(runLog.final_course ?? previewData, null, 2);
    }
    if (logTab === 'agents') {
      return JSON.stringify(
        {
          course_from_agents: runLog.course_from_agents,
          crew_tasks: runLog.crew_tasks,
          agent_raw_output: runLog.agent_raw_output,
          repairs: runLog.repairs,
        },
        null,
        2
      );
    }
    return runLog.verbose_trace || '(no verbose trace captured)';
  })();

  if (!currentModule) {
    return (
      <div
        className="flex h-full items-center justify-center bg-[color:var(--rp-bg)] text-[color:var(--rp-muted)]"
        style={{ fontFamily: 'var(--rp-font-body)' }}
      >
        No modules in this course preview.
      </div>
    );
  }

  return (
    <div className="relative flex h-full min-h-0 w-full overflow-hidden bg-[color:var(--rp-bg)] text-[color:var(--rp-ink)]">
      <aside className="flex w-72 shrink-0 flex-col border-r border-[color:var(--rp-stone-border)] bg-[color:var(--rp-bg-warm)]/80 sm:w-80">
        <div className="border-b border-[color:var(--rp-stone-border)] p-6">
          <p
            className="text-[10px] uppercase tracking-[0.2em] text-[color:var(--rp-accent)]"
            style={{ fontFamily: 'var(--rp-font-display)' }}
          >
            Course preview
            {previewData.category
              ? ` · ${TOPIC_CATEGORY_LABELS[previewData.category] ?? previewData.category}`
              : ''}
          </p>
          <h1
            className="mt-3 text-xl font-semibold leading-snug tracking-tight text-[color:var(--rp-ink)]"
            style={{ fontFamily: 'var(--rp-font-display)' }}
          >
            {previewData.title}
          </h1>
          <p
            className="mt-3 line-clamp-4 text-sm leading-relaxed text-[color:var(--rp-muted)]"
            style={{ fontFamily: 'var(--rp-font-body)' }}
          >
            {previewData.description}
          </p>
        </div>

        <nav className="flex-1 space-y-0.5 overflow-y-auto p-3">
          {previewData.modules.map((module, idx) => {
            const active = activeModuleIndex === idx;
            return (
              <button
                key={idx}
                type="button"
                onClick={() => setActiveModuleIndex(idx)}
                className={`w-full border-l-2 px-4 py-3 text-left transition ${
                  active
                    ? 'border-[color:var(--rp-accent)] bg-[color:var(--rp-stone)]/50 text-[color:var(--rp-highlight)]'
                    : 'border-transparent text-[color:var(--rp-muted)] hover:border-[color:var(--rp-stone-border)] hover:text-[color:var(--rp-ink)]'
                }`}
              >
                <span
                  className="block text-[10px] uppercase tracking-[0.16em] opacity-70"
                  style={{ fontFamily: 'var(--rp-font-display)' }}
                >
                  Module {idx + 1}
                  {module.is_primary_sources_only ? ' · Primary sources' : ''}
                  {module.is_legacy_module ? ' · Legacy' : ''}
                </span>
                <span
                  className="mt-1 block text-sm font-medium leading-snug"
                  style={{ fontFamily: 'var(--rp-font-display)' }}
                >
                  {module.module_title}
                </span>
              </button>
            );
          })}
        </nav>

        <div className="space-y-2 border-t border-[color:var(--rp-stone-border)] p-4">
          <div className="flex gap-2">
            <button
              type="button"
              onClick={handleConfirm}
              disabled={busy}
              className="flex-1 bg-[color:var(--rp-accent)] py-3 text-sm font-semibold tracking-wide text-[color:var(--rp-bg)] transition enabled:hover:brightness-110 disabled:opacity-60"
              style={{ fontFamily: 'var(--rp-font-display)' }}
            >
              {busy ? 'Saving…' : 'Save course'}
            </button>
            <button
              type="button"
              onClick={onRegenerate}
              disabled={busy}
              className="flex-1 border border-[color:var(--rp-stone-border)] py-3 text-sm tracking-wide text-[color:var(--rp-highlight)] transition hover:border-[color:var(--rp-accent)] hover:text-[color:var(--rp-accent)] disabled:opacity-60"
              style={{ fontFamily: 'var(--rp-font-display)' }}
            >
              Regenerate
            </button>
          </div>
          {jobId && (
            <button
              type="button"
              onClick={handleOpenLog}
              className="w-full border border-[color:var(--rp-stone-border)] py-2.5 text-xs tracking-wide text-[color:var(--rp-muted)] transition hover:border-[color:var(--rp-accent)] hover:text-[color:var(--rp-accent)]"
              style={{ fontFamily: 'var(--rp-font-display)' }}
            >
              View agent log
            </button>
          )}
        </div>
      </aside>

      <main className="min-h-0 flex-1 overflow-y-auto px-6 py-8 sm:px-10 sm:py-10">
        <div className="mx-auto max-w-2xl">
          <h2
            className="text-2xl font-semibold tracking-tight text-[color:var(--rp-ink)] sm:text-3xl"
            style={{ fontFamily: 'var(--rp-font-display)' }}
          >
            {currentModule.module_title}
          </h2>
          {currentModule.is_primary_sources_only && (
            <p
              className="mt-3 text-sm text-[color:var(--rp-accent)]"
              style={{ fontFamily: 'var(--rp-font-body)' }}
            >
              Primary sources only — learn this period through what people then wrote.
            </p>
          )}
          {currentModule.is_legacy_module && (
            <p
              className="mt-3 text-sm text-[color:var(--rp-accent)]"
              style={{ fontFamily: 'var(--rp-font-body)' }}
            >
              Legacy module — founders and early works that shaped the field.
            </p>
          )}

          <section className="mt-10">
            <h3
              className="text-[11px] uppercase tracking-[0.2em] text-[color:var(--rp-accent)]"
              style={{ fontFamily: 'var(--rp-font-display)' }}
            >
              Learning objectives
            </h3>
            <ul
              className="mt-4 space-y-3 text-[color:var(--rp-ink)]/90"
              style={{ fontFamily: 'var(--rp-font-body)' }}
            >
              {currentModule.learning_objectives.map((obj, i) => (
                <li key={i} className="flex gap-3 leading-relaxed">
                  <span className="mt-2 h-1 w-1 shrink-0 rounded-full bg-[color:var(--rp-accent)]" />
                  <span>{obj}</span>
                </li>
              ))}
            </ul>
          </section>

          <section className="mt-12">
            <h3
              className="text-[11px] uppercase tracking-[0.2em] text-[color:var(--rp-accent)]"
              style={{ fontFamily: 'var(--rp-font-display)' }}
            >
              Assigned readings
            </h3>
            <div className="mt-4 space-y-3">
              {currentModule.assigned_readings.map((book, i) => (
                <article
                  key={i}
                  className="border border-[color:var(--rp-stone-border)] bg-[color:var(--rp-bg-warm)]/40 px-5 py-5"
                >
                  <p
                    className="font-semibold text-[color:var(--rp-ink)]"
                    style={{ fontFamily: 'var(--rp-font-display)' }}
                  >
                    {book.title}
                  </p>
                  <p
                    className="mt-1 text-sm text-[color:var(--rp-muted)]"
                    style={{ fontFamily: 'var(--rp-font-body)' }}
                  >
                    {book.authors}
                    {book.published_year ? ` · ${book.published_year}` : ''}
                  </p>
                  {book.link && (
                    <a
                      href={book.link}
                      target="_blank"
                      rel="noreferrer"
                      className="mt-3 mr-4 inline-block text-sm text-[color:var(--rp-accent)] underline decoration-[color:var(--rp-stone-border)] underline-offset-4 transition hover:text-[color:var(--rp-highlight)] hover:decoration-[color:var(--rp-accent)]"
                      style={{ fontFamily: 'var(--rp-font-body)' }}
                    >
                      View catalog listing →
                    </a>
                  )}
                  {book.gutenberg_url && (
                    <a
                      href={book.gutenberg_url}
                      target="_blank"
                      rel="noreferrer"
                      className="mt-3 inline-block text-sm text-[color:var(--rp-highlight)] underline decoration-[color:var(--rp-stone-border)] underline-offset-4 transition hover:text-[color:var(--rp-accent)] hover:decoration-[color:var(--rp-accent)]"
                      style={{ fontFamily: 'var(--rp-font-body)' }}
                    >
                      Read free (Gutenberg) →
                    </a>
                  )}
                </article>
              ))}
            </div>
          </section>

          <section className="mt-12 pb-8">
            <h3
              className="text-[11px] uppercase tracking-[0.2em] text-[color:var(--rp-accent)]"
              style={{ fontFamily: 'var(--rp-font-display)' }}
            >
              Assignments
            </h3>
            <div className="mt-4 space-y-4">
              {currentModule.assignments.map((assignment, i) => (
                <article
                  key={i}
                  className="border border-[color:var(--rp-stone-border)] bg-[color:var(--rp-bg-warm)]/40 px-5 py-5"
                >
                  <p
                    className="text-lg font-medium text-[color:var(--rp-highlight)]"
                    style={{ fontFamily: 'var(--rp-font-display)' }}
                  >
                    {assignment.assignment_title}
                  </p>
                  <p
                    className="mt-3 leading-relaxed text-[color:var(--rp-muted)]"
                    style={{ fontFamily: 'var(--rp-font-body)' }}
                  >
                    {assignment.description}
                  </p>
                </article>
              ))}
            </div>
          </section>
        </div>
      </main>

      {showLog && (
        <div className="absolute inset-0 z-20 flex flex-col bg-[color:var(--rp-bg)]/95 backdrop-blur-sm">
          <div className="flex items-center justify-between border-b border-[color:var(--rp-stone-border)] px-5 py-4">
            <div>
              <p
                className="text-[10px] uppercase tracking-[0.2em] text-[color:var(--rp-accent)]"
                style={{ fontFamily: 'var(--rp-font-display)' }}
              >
                Agent run log
              </p>
              <p
                className="mt-1 text-sm text-[color:var(--rp-muted)]"
                style={{ fontFamily: 'var(--rp-font-body)' }}
              >
                {runLog?.files?.run
                  ? `Also on disk: ${runLog.files.run}`
                  : jobId
                    ? `Job ${jobId}`
                    : ''}
              </p>
            </div>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={handleCopyLog}
                disabled={!runLog}
                className="border border-[color:var(--rp-stone-border)] px-3 py-1.5 text-xs tracking-wide text-[color:var(--rp-highlight)] transition hover:border-[color:var(--rp-accent)] disabled:opacity-50"
                style={{ fontFamily: 'var(--rp-font-display)' }}
              >
                Copy JSON
              </button>
              <button
                type="button"
                onClick={() => setShowLog(false)}
                className="border border-[color:var(--rp-stone-border)] px-3 py-1.5 text-xs tracking-wide text-[color:var(--rp-muted)] transition hover:border-[color:var(--rp-accent)] hover:text-[color:var(--rp-accent)]"
                style={{ fontFamily: 'var(--rp-font-display)' }}
              >
                Close
              </button>
            </div>
          </div>

          <div className="flex gap-2 border-b border-[color:var(--rp-stone-border)] px-5 py-2">
            {(
              [
                ['final', 'Final course'],
                ['agents', 'Agent output'],
                ['verbose', 'Verbose trace'],
              ] as const
            ).map(([key, label]) => (
              <button
                key={key}
                type="button"
                onClick={() => setLogTab(key)}
                className={`px-3 py-1.5 text-xs tracking-wide transition ${
                  logTab === key
                    ? 'text-[color:var(--rp-accent)]'
                    : 'text-[color:var(--rp-muted)] hover:text-[color:var(--rp-highlight)]'
                }`}
                style={{ fontFamily: 'var(--rp-font-display)' }}
              >
                {label}
              </button>
            ))}
          </div>

          <div className="min-h-0 flex-1 overflow-auto p-5">
            {logLoading && (
              <p
                className="text-sm text-[color:var(--rp-muted)]"
                style={{ fontFamily: 'var(--rp-font-body)' }}
              >
                Loading log…
              </p>
            )}
            {logError && (
              <p
                className="text-sm text-[#d4a09a]"
                style={{ fontFamily: 'var(--rp-font-body)' }}
              >
                {logError}
              </p>
            )}
            {!logLoading && !logError && (
              <pre
                className="whitespace-pre-wrap break-words text-xs leading-relaxed text-[color:var(--rp-ink)]/90"
                style={{
                  fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace',
                }}
              >
                {logBody}
              </pre>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
