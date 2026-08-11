import React, { useState, useRef, useEffect, type ChangeEvent, type KeyboardEvent } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { crewApi, courseApi, type CoursePreviewData } from '../lib/api';
import { CoursePreview } from './CoursePreview';
import { useAuth } from '../lib/auth';

interface HeroSectionProps {
  onCourseSaved?: () => void;
}

export const HeroSection: React.FC<HeroSectionProps> = ({ onCourseSaved }) => {
  const [input, setInput] = useState('');
  const [previewData, setPreviewData] = useState<CoursePreviewData | null>(null);
  const [isPreviewing, setIsPreviewing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const { isAuthenticated, login, logout, user } = useAuth();
  const queryClient = useQueryClient();

  const previewMutation = useMutation({
    mutationFn: (topic: string) => crewApi.kickoffCrew(topic),
    onSuccess: (data) => {
      setPreviewData({ ...data, topic: data.topic || input.trim() });
      setIsPreviewing(true);
      setError(null);
    },
    onError: (err: unknown) => {
      const message =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail || 'Failed to generate course. Try again.';
      setError(String(message));
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
    setIsPreviewing(false);
    setInput('');
    setError(null);
  };

  const handleConfirm = async () => {
    if (!previewData) return;
    await saveMutation.mutateAsync(previewData);
  };

  const suggestions = [
    'Medieval European History',
    'Machine Learning Fundamentals',
    'Stoicism and Modern Life',
  ];

  return (
    <section className="relative min-h-screen w-full flex items-center justify-center bg-[#09090b] text-white px-6 py-12 overflow-hidden">
      <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-indigo-600/10 rounded-full blur-[140px] pointer-events-none" />
      <div className="absolute top-1/2 left-1/3 w-[400px] h-[400px] bg-sky-500/5 rounded-full blur-[120px] pointer-events-none" />

      <div className="absolute top-6 right-6 z-20 flex items-center gap-3">
        {user ? (
          <>
            <span className="text-sm text-zinc-400">{user.name || user.email}</span>
            <button
              onClick={logout}
              className="px-3 py-2 text-xs rounded-xl bg-zinc-900 text-zinc-300 border border-zinc-800 hover:bg-zinc-800"
            >
              Sign out
            </button>
          </>
        ) : (
          <button
            onClick={login}
            className="px-4 py-2 text-sm rounded-xl bg-white text-black font-medium hover:bg-zinc-200 transition"
          >
            Sign in with Google
          </button>
        )}
      </div>

      <div className="relative z-10 w-full max-w-[1280px] flex flex-col items-center">
        {!isPreviewing ? (
          <>
            <div className="inline-flex items-center gap-2 px-3 py-1 text-xs font-medium bg-zinc-900 border border-zinc-800 rounded-full text-zinc-400 mb-6 tracking-wide">
              <span className="h-1.5 w-1.5 rounded-full bg-indigo-400" />
              Now in Beta
            </div>

            <h1 className="text-4xl sm:text-6xl font-bold tracking-tight mb-6 bg-clip-text text-transparent bg-gradient-to-b from-white to-zinc-400 leading-[1.15]">
              Turn any topic <br />
              <span className="bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400">
                into a real reading journey.
              </span>
            </h1>

            <p className="text-zinc-400 text-base sm:text-lg max-w-xl mb-10 leading-relaxed font-normal">
              Enter a topic. Get a structured course with real books, thoughtful
              assignments, and no AI summaries.
            </p>

            <div className="w-full relative group max-w-2xl">
              <div className="absolute -inset-px bg-gradient-to-r from-indigo-500 to-purple-500 rounded-2xl opacity-30 group-focus-within:opacity-70 blur-sm transition duration-300" />

              <div className="relative flex items-end gap-2 p-3 bg-zinc-950/80 border border-zinc-800 rounded-2xl shadow-2xl backdrop-blur-md">
                <textarea
                  ref={textareaRef}
                  rows={1}
                  value={input}
                  onChange={handleInputChange}
                  onKeyDown={handleKeyDown}
                  placeholder={
                    isAuthenticated
                      ? 'Enter a topic you want to master...'
                      : 'Sign in to generate a course...'
                  }
                  className="flex-1 max-h-48 min-h-[24px] py-1.5 resize-none bg-transparent text-zinc-100 placeholder-zinc-500 focus:outline-none text-[15px] leading-relaxed"
                />

                <button
                  onClick={handleSend}
                  disabled={!input.trim() || previewMutation.isPending}
                  className={`flex items-center justify-center p-2.5 rounded-xl transition-all duration-200 
                    ${
                      !input.trim() || previewMutation.isPending
                        ? 'bg-zinc-900 text-zinc-600 cursor-not-allowed'
                        : 'bg-white hover:bg-zinc-200 text-black shadow-md shadow-white/10 active:scale-95'
                    }`}
                >
                  {previewMutation.isPending ? '…' : '→'}
                </button>
              </div>
            </div>

            {previewMutation.isPending && (
              <p className="mt-4 text-sm text-zinc-400">
                Building your course from real books — this can take a minute…
              </p>
            )}

            {error && (
              <p className="mt-4 text-sm text-rose-400 max-w-xl text-center">{error}</p>
            )}

            <div className="flex flex-wrap items-center justify-center gap-2 mt-5">
              <span className="text-xs text-zinc-500 mr-1">Try:</span>
              {suggestions.map((suggestion, index) => (
                <button
                  key={index}
                  onClick={() => setInput(suggestion)}
                  className="px-3 py-1 rounded-lg text-xs text-zinc-400 bg-zinc-900/40 hover:bg-zinc-900 border border-zinc-800/80 hover:border-zinc-700 hover:text-zinc-200 transition-all duration-150 active:scale-95"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </>
        ) : (
          <div className="w-full h-[88vh] rounded-3xl overflow-hidden shadow-2xl border border-neutral-700">
            {error && (
              <p className="p-3 text-sm text-rose-400 bg-neutral-950 border-b border-neutral-800">
                {error}
              </p>
            )}
            <CoursePreview
              previewData={previewData!}
              onConfirm={handleConfirm}
              onRegenerate={handleRegenerate}
              isSaving={saveMutation.isPending}
            />
          </div>
        )}
      </div>
    </section>
  );
};
