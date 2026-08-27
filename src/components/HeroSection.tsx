import React, { useState, useRef, useEffect, type ChangeEvent, type KeyboardEvent } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
  crewApi,
  courseApi,
  type CoursePreviewData,
  type CrewJobStep,
} from '../lib/api';
import { CoursePreview } from './CoursePreview';
import { ConstellationBackdrop } from './ConstellationBackdrop';
import { useAuth } from '../lib/auth';

interface HeroSectionProps {
  onCourseSaved?: () => void;
}

const POLL_MS = 1000;

async function runCrewJobWithProgress(
  topic: string,
  onSteps: (steps: CrewJobStep[]) => void
): Promise<{ course: CoursePreviewData; jobId: string }> {
  const { job_id } = await crewApi.createJob(topic);

  for (;;) {
    const job = await crewApi.getJob(job_id);
    onSteps(job.steps || []);

    if (job.status === 'complete' && job.result) {
      return { course: job.result, jobId: job_id };
    }
    if (job.status === 'failed') {
      throw new Error(job.error || 'Course generation failed.');
    }

    await new Promise((resolve) => setTimeout(resolve, POLL_MS));
  }
}

export const HeroSection: React.FC<HeroSectionProps> = ({ onCourseSaved }) => {
  const [input, setInput] = useState('');
  const [previewData, setPreviewData] = useState<CoursePreviewData | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [isPreviewing, setIsPreviewing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [jobSteps, setJobSteps] = useState<CrewJobStep[]>([]);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const { isAuthenticated, login, logout, user } = useAuth();
  const queryClient = useQueryClient();

  const previewMutation = useMutation({
    mutationFn: (topic: string) =>
      runCrewJobWithProgress(topic, (steps) => setJobSteps(steps)),
    onSuccess: ({ course, jobId: id }) => {
      setPreviewData({ ...course, topic: course.topic || input.trim() });
      setJobId(id);
      setIsPreviewing(true);
      setError(null);
      setJobSteps([]);
    },
    onError: (err: unknown) => {
      const message =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ||
        (err instanceof Error ? err.message : null) ||
        'Failed to generate course. Try again.';
      setError(String(message));
      setJobSteps([]);
    },
  });

  const saveMutation = useMutation({
    mutationFn: async (course: CoursePreviewData) => {
      return courseApi.createCourse({
        title: course.title,
        description: course.description,
        topic: course.topic || input.trim() || course.title,
        modules: course.modules,
      });
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['userGraph'] });
      setIsPreviewing(false);
      setPreviewData(null);
      setJobId(null);
      setInput('');
      onCourseSaved?.();
    },
    onError: (err: unknown) => {
      const message =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail || 'Failed to save course.';
      setError(String(message));
    },
  });

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [input]);

  const handleInputChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
  };

  const handleSend = () => {
    if (!input.trim()) return;
    if (!isAuthenticated) {
      login();
      return;
    }
    setError(null);
    setJobSteps([
      { key: 'classifying_topic', label: 'Classifying topic', status: 'pending' },
      {
        key: 'searching_books',
        label: 'Searching verified catalogs',
        status: 'pending',
      },
      {
        key: 'building_modules',
        label: 'Building course modules',
        status: 'pending',
      },
      {
        key: 'validating_readings',
        label: 'Validating & repairing readings',
        status: 'pending',
      },
    ]);
    previewMutation.mutate(input.trim());
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleRegenerate = () => {
    setPreviewData(null);
    setJobId(null);
    setIsPreviewing(false);
    setInput('');
    setError(null);
    setJobSteps([]);
  };

  const handleConfirm = async () => {
    if (!previewData) return;
    await saveMutation.mutateAsync(previewData);
  };

  if (isPreviewing && previewData) {
    return (
      <section className="rp-hero-bg relative min-h-screen w-full overflow-hidden px-4 py-6 sm:px-8 sm:py-10">
        <ConstellationBackdrop />
        <div className="relative z-10 mx-auto flex h-[min(90vh,920px)] max-w-6xl flex-col overflow-hidden rounded-sm border border-[color:var(--rp-stone-border)] bg-[color:var(--rp-bg)]/80 shadow-[0_24px_80px_rgba(0,0,0,0.55)] backdrop-blur-sm">
          {error && (
            <p className="border-b border-[color:var(--rp-stone-border)] bg-[color:var(--rp-bg-warm)] px-4 py-3 text-sm text-[#d4a09a]">
              {error}
            </p>
          )}
          <div className="min-h-0 flex-1 overflow-hidden">
            <CoursePreview
              previewData={previewData}
              jobId={jobId}
              onConfirm={handleConfirm}
              onRegenerate={handleRegenerate}
              isSaving={saveMutation.isPending}
            />
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className="rp-hero-bg relative flex min-h-screen w-full flex-col overflow-hidden text-[color:var(--rp-ink)]">
      <ConstellationBackdrop />
      <header className="relative z-20 flex items-center justify-end px-6 py-6 sm:px-10">
        {user ? (
          <div className="flex items-center gap-4">
            <span
              className="max-w-[12rem] truncate text-sm text-[color:var(--rp-muted)]"
              style={{ fontFamily: 'var(--rp-font-body)' }}
            >
              {user.name || user.email}
            </span>
            <button
              type="button"
              onClick={logout}
              className="border border-[color:var(--rp-stone-border)] px-3 py-1.5 text-xs tracking-wide text-[color:var(--rp-highlight)] transition hover:border-[color:var(--rp-accent)] hover:text-[color:var(--rp-accent)]"
            >
              Sign out
            </button>
          </div>
        ) : (
          <button
            type="button"
            onClick={login}
            className="border border-[color:var(--rp-stone-border)] px-4 py-2 text-sm tracking-wide text-[color:var(--rp-highlight)] transition hover:border-[color:var(--rp-accent)] hover:text-[color:var(--rp-accent)]"
          >
            Sign in with Google
          </button>
        )}
      </header>

      <div className="relative z-10 mx-auto flex w-full max-w-3xl flex-1 flex-col items-center justify-center px-6 pb-24 pt-4 text-center sm:px-8">
        <h1
          className="rp-rise text-[clamp(3rem,12vw,6.5rem)] font-extrabold leading-[0.95] tracking-[-0.04em] text-[color:var(--rp-ink)]"
          style={{ fontFamily: 'var(--rp-font-display)' }}
        >
          ReaderPath
        </h1>

        <p
          className="rp-rise rp-rise-delay-1 mt-6 text-[clamp(1.25rem,3vw,1.75rem)] font-medium tracking-tight text-[color:var(--rp-highlight)]"
          style={{ fontFamily: 'var(--rp-font-display)' }}
        >
          A course of real books.
        </p>

        <p
          className="rp-rise rp-rise-delay-2 mt-4 max-w-md text-base leading-relaxed text-[color:var(--rp-muted)] sm:text-lg"
          style={{ fontFamily: 'var(--rp-font-body)' }}
        >
          Enter a topic. Read primary sources. Think for yourself.
        </p>

        <div className="rp-rise rp-rise-delay-3 mt-12 w-full max-w-xl">
          {previewMutation.isPending ? (
            <div
              className="flex flex-col items-center gap-6 border border-[color:var(--rp-stone-border)] bg-[color:var(--rp-bg)]/55 px-6 py-10 backdrop-blur-md"
              role="status"
              aria-live="polite"
              aria-busy="true"
            >
              <div className="rp-loader" aria-hidden>
                <span />
                <span />
                <span />
              </div>
              <div className="space-y-2 text-center">
                <p
                  className="text-base tracking-wide text-[color:var(--rp-highlight)]"
                  style={{ fontFamily: 'var(--rp-font-display)' }}
                >
                  Building your course
                </p>
                <p
                  className="text-sm leading-relaxed text-[color:var(--rp-muted)]"
                  style={{ fontFamily: 'var(--rp-font-body)' }}
                >
                  Gathering real books for “{input.trim()}” — this can take a
                  minute…
                </p>
              </div>
              <ol className="w-full max-w-sm space-y-2 text-left">
                {jobSteps.map((step) => {
                  const isActive = step.status === 'active';
                  const isDone = step.status === 'done';
                  const isFailed = step.status === 'failed';
                  return (
                    <li
                      key={step.key}
                      className={`flex items-center gap-3 border-l-2 pl-3 text-sm ${
                        isActive
                          ? 'border-[color:var(--rp-accent)] text-[color:var(--rp-highlight)]'
                          : isDone
                            ? 'border-[color:var(--rp-accent)]/40 text-[color:var(--rp-muted)]'
                            : isFailed
                              ? 'border-[#d4a09a] text-[#d4a09a]'
                              : 'border-[color:var(--rp-stone-border)] text-[color:var(--rp-muted)]/60'
                      }`}
                      style={{ fontFamily: 'var(--rp-font-body)' }}
                    >
                      <span
                        className="w-4 shrink-0 text-center text-xs"
                        aria-hidden
                      >
                        {isDone ? '✓' : isActive ? '●' : isFailed ? '!' : '○'}
                      </span>
                      <span>{step.label}</span>
                    </li>
                  );
                })}
              </ol>
            </div>
          ) : (
            <div className="rp-input flex items-end gap-2 border border-[color:var(--rp-stone-border)] bg-[color:var(--rp-bg)]/55 px-3 py-3 backdrop-blur-md transition">
              <textarea
                ref={textareaRef}
                rows={1}
                value={input}
                onChange={handleInputChange}
                onKeyDown={handleKeyDown}
                placeholder={
                  isAuthenticated
                    ? 'Enter a topic you want to master…'
                    : 'Sign in to begin a reading journey…'
                }
                className="max-h-40 min-h-[28px] flex-1 resize-none bg-transparent py-1.5 text-left text-[15px] leading-relaxed text-[color:var(--rp-ink)] placeholder:text-[color:var(--rp-muted)] focus:outline-none"
                style={{ fontFamily: 'var(--rp-font-body)' }}
              />
              <button
                type="button"
                onClick={handleSend}
                disabled={!input.trim()}
                aria-label="Generate course"
                className="rp-send flex h-10 w-10 shrink-0 items-center justify-center bg-[color:var(--rp-accent)] text-[color:var(--rp-bg)] transition enabled:hover:brightness-110 disabled:cursor-not-allowed disabled:bg-[color:var(--rp-stone)] disabled:text-[color:var(--rp-muted)]"
              >
                →
              </button>
            </div>
          )}

          {error && !previewMutation.isPending && (
            <p className="mt-4 text-sm text-[#d4a09a]">{error}</p>
          )}
        </div>

        {!previewMutation.isPending && (
          <p
            className="mt-16 max-w-lg text-xs leading-relaxed text-[color:var(--rp-muted)]/70"
            style={{ fontFamily: 'var(--rp-font-body)' }}
          >
            {[
              'Medieval European History',
              'Machine Learning Fundamentals',
              'Stoicism and Modern Life',
            ].map((topic, i, arr) => (
              <span key={topic}>
                <button
                  type="button"
                  onClick={() => setInput(topic)}
                  className="underline decoration-[color:var(--rp-stone-border)] underline-offset-4 transition hover:text-[color:var(--rp-highlight)] hover:decoration-[color:var(--rp-accent)]"
                >
                  {topic}
                </button>
                {i < arr.length - 1 ? ' · ' : ''}
              </span>
            ))}
          </p>
        )}
      </div>
    </section>
  );
};
