import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Routes, Route, useNavigate, useParams } from 'react-router-dom';
import { graphApi } from './lib/api';
import { useAuth } from './lib/auth';
import HomeGraph from './components/HomeGraph';
import { HeroSection } from './components/HeroSection';

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
    return (
      <div className="flex h-screen items-center justify-center bg-neutral-950 text-zinc-400">
        Loading…
      </div>
    );
  }

  const hasCourses =
    Boolean(graphData?.nodes?.some((n) => n.type === 'Course')) &&
    Boolean(graphData?.nodes?.length);

  if (isAuthenticated && !forceHero && isPending) {
    return (
      <div className="flex h-screen items-center justify-center bg-neutral-950 text-zinc-400">
        Loading your learning graph…
      </div>
    );
  }

  if (isAuthenticated && !forceHero && error) {
    // New users with no graph yet may 401/empty — fall through to hero if no courses
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
    <div className="min-h-screen bg-neutral-950">
      {isAuthenticated && hasCourses && (
        <div className="absolute top-6 left-6 z-30">
          <button
            onClick={() => {
              setForceHero(false);
              navigate('/');
            }}
            className="px-3 py-2 text-xs rounded-xl bg-slate-800 text-slate-200 border border-slate-700"
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
    return (
      <div className="flex h-screen items-center justify-center bg-neutral-950 text-zinc-400">
        Loading shared graph…
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex h-screen items-center justify-center bg-neutral-950 text-rose-400">
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
