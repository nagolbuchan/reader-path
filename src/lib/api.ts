import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

export interface SessionUser {
  user_id: string;
  email?: string;
  name?: string;
  image?: string;
}

export interface BookReading {
  title: string;
  authors: string;
  link?: string;
  summary?: string;
  google_books_id?: string;
  open_library_id?: string;
  isbn13?: string;
  gutenberg_url?: string;
  published_year?: number;
}

export interface AssignmentItem {
  assignment_title: string;
  description: string;
}

export interface ModuleItem {
  module_title: string;
  learning_objectives: string[];
  assigned_readings: BookReading[];
  assignments: AssignmentItem[];
  is_primary_sources_only?: boolean;
  is_legacy_module?: boolean;
}

export type TopicCategory =
  | 'history'
  | 'sciences'
  | 'trade_craft'
  | 'philosophy'
  | 'literature'
  | 'languages'
  | 'professional'
  | 'religion_theology'
  | 'other';

export const TOPIC_CATEGORY_LABELS: Record<TopicCategory, string> = {
  history: 'History',
  sciences: 'Sciences',
  trade_craft: 'Trade / Craft',
  philosophy: 'Philosophy',
  literature: 'Literature',
  languages: 'Languages',
  professional: 'Professional',
  religion_theology: 'Religion / Theology',
  other: 'Other',
};

export interface CoursePreviewData {
  id?: string;
  title: string;
  description: string;
  topic?: string;
  category?: TopicCategory;
  modules: ModuleItem[];
  /** Unused verified books from this generation, for quick reading replacement. */
  replacement_pool?: BookReading[];
}

export type CrewJobStepStatus = 'pending' | 'active' | 'done' | 'failed';

export interface CrewJobStep {
  key: string;
  label: string;
  status: CrewJobStepStatus;
}

export interface CrewJobStatus {
  job_id: string;
  topic: string;
  status: 'pending' | 'running' | 'complete' | 'failed';
  steps: CrewJobStep[];
  result?: CoursePreviewData | null;
  error?: string | null;
  log_available?: boolean;
  created_at?: string;
}

export interface CrewRunLog {
  run_id: string;
  topic: string;
  category?: string | null;
  status: string;
  started_at?: string;
  finished_at?: string | null;
  files?: Record<string, string>;
  verbose_trace?: string;
  agent_steps?: unknown[];
  crew_tasks?: unknown[];
  agent_raw_output?: string | null;
  course_from_agents?: CoursePreviewData | null;
  repairs?: string[];
  final_course?: CoursePreviewData | null;
  error?: string | null;
}

export interface GraphPayload {
  nodes: Array<{
    id: string;
    type: string;
    label: string;
    properties?: Record<string, unknown>;
  }>;
  relationships: Array<{
    from: string;
    to: string;
    type: string;
  }>;
}

export const authApi = {
  getSession: async (): Promise<{ user: SessionUser | null }> => {
    const response = await api.get('/auth/session');
    return response.data;
  },
  logout: async () => {
    const response = await api.post('/auth/logout');
    return response.data;
  },
  loginUrl: () => `${API_BASE_URL}/auth/login`,
};

export const graphApi = {
  getUserGraph: async (): Promise<GraphPayload> => {
    const response = await api.get('/graph/user-graph');
    return response.data;
  },
  getPublicUserGraph: async (userId: string): Promise<GraphPayload> => {
    const response = await api.get(`/graph/users/${encodeURIComponent(userId)}`);
    return response.data;
  },
};

export const courseApi = {
  createCourse: async (course: {
    title: string;
    description: string;
    topic: string;
    modules: ModuleItem[];
  }) => {
    const response = await api.post('/courses', course);
    return response.data as {
      course_id: string;
      title: string;
      description: string;
      topic: string;
    };
  },
  getUserCourses: async () => {
    const response = await api.get('/courses');
    return response.data;
  },
};

export const crewApi = {
  kickoffCrew: async (topic: string): Promise<CoursePreviewData> => {
    const response = await api.get(
      `/crew/kickoff?topic=${encodeURIComponent(topic)}`
    );
    const payload = response.data;
    if (payload?.data) {
      return payload.data as CoursePreviewData;
    }
    return payload as CoursePreviewData;
  },
  createJob: async (topic: string): Promise<{ job_id: string; status: string }> => {
    const response = await api.post('/crew/jobs', { topic });
    return response.data;
  },
  getJob: async (jobId: string): Promise<CrewJobStatus> => {
    const response = await api.get(`/crew/jobs/${encodeURIComponent(jobId)}`);
    return response.data as CrewJobStatus;
  },
  getJobLog: async (jobId: string): Promise<CrewRunLog> => {
    const response = await api.get(
      `/crew/jobs/${encodeURIComponent(jobId)}/log`
    );
    return response.data as CrewRunLog;
  },
  getReplacementPool: async (
    jobId: string
  ): Promise<{ job_id: string; books: BookReading[]; count: number }> => {
    const response = await api.get(
      `/crew/jobs/${encodeURIComponent(jobId)}/replacement-pool`
    );
    return response.data;
  },
};

export default api;
