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
}

export interface CoursePreviewData {
  id?: string;
  title: string;
  description: string;
  topic?: string;
  modules: ModuleItem[];
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
};

export default api;
