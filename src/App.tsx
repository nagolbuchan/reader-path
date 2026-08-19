import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Routes, Route, useNavigate, useParams } from 'react-router-dom';
import { graphApi } from './lib/api';
import { useAuth } from './lib/auth';
import HomeGraph from './components/HomeGraph';
import { HeroSection } from './components/HeroSection';

function LoadingScreen({ label }: { label: string }) {
  return (
    <div
      className="flex h-screen items-center justify-center bg-[color:var(--rp-bg)] text-[color:var(--rp-muted)]"
      style={{ fontFamily: 'var(--rp-font-body)' }}
    >
      {label}
    </div>
  );
}

function HomePage() {
  const { user, isLoading: authLoading, isAuthenticated, logout } = useAuth();
  const [forceHero, setForceHero] = useState(false);
  const navigate = useNavigate();

  const {
    data: graphData,
    isPending,
    error,
    refetch,
  } = useQuery({
    queryKey: ['userGraph', user?.user_id],
    queryFn: graphApi.getUserGraph,
    enabled: isAuthenticated,
    staleTime: 1000 * 60 * 2,
    retry: false,
  });

  if (authLoading) {
    return <LoadingScreen label="Loading…" />;
  }

  const hasCourses =
    Boolean(graphData?.nodes?.some((n) => n.type === 'Course')) &&
    Boolean(graphData?.nodes?.length);

  if (isAuthenticated && !forceHero && isPending) {
    return <LoadingScreen label="Opening your learning graph…" />;
  }

  if (isAuthenticated && !forceHero && error) {
    // Fall through to hero if graph fetch fails / empty
  }

  if (isAuthenticated && !forceHero && hasCourses && graphData) {
    const shareUrl = `${window.location.origin}/u/${encodeURIComponent(user!.user_id)}`;
    return (
      <HomeGraph
        graphData={graphData}
        shareUrl={shareUrl}
        onCreateCourse={() => setForceHero(true)}
        onLogout={logout}
      />
    );
  }

  return (
    <div className="min-h-screen bg-[color:var(--rp-bg)]">
      {isAuthenticated && hasCourses && (
        <div className="absolute top-6 left-6 z-30">
          <button
            type="button"
            onClick={() => {
              setForceHero(false);
              navigate('/');
            }}
            className="border border-[color:var(--rp-stone-border)] bg-[color:var(--rp-bg)]/70 px-3 py-2 text-xs tracking-wide text-[color:var(--rp-highlight)] backdrop-blur-sm transition hover:border-[color:var(--rp-accent)] hover:text-[color:var(--rp-accent)]"
          >
            Back to graph
          </button>
        </div>
      )}
      <HeroSection
        onCourseSaved={() => {
          setForceHero(false);
          refetch();
        }}
      />
    </div>
  );
}

function PublicGraphPage() {
  const { userId } = useParams<{ userId: string }>();
  const { data, isPending, error } = useQuery({
    queryKey: ['publicGraph', userId],
    queryFn: () => graphApi.getPublicUserGraph(userId!),
    enabled: Boolean(userId),
    retry: false,
  });

  if (isPending) {
    return <LoadingScreen label="Loading shared graph…" />;
  }

  if (error || !data) {
    return (
      <div
        className="flex h-screen items-center justify-center bg-[color:var(--rp-bg)] text-[#d4a09a]"
        style={{ fontFamily: 'var(--rp-font-body)' }}
      >
        Shared graph not found.
      </div>
    );
  }

  return <HomeGraph graphData={data} readOnly />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/u/:userId" element={<PublicGraphPage />} />
    </Routes>
  );
}
