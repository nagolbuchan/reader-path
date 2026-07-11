import axios from 'axios';

//Confirm what the base url is
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
    // withCredentials: true, // Include cookies for authentication if needed
});

// Add a request interceptor to include authentication token if available
// api.interceptors.request.use((config) => {
//   const token = localStorage.getItem('auth_token'); // or use Clerk/Auth.js token
//   if (token) {
//     config.headers.Authorization = `Bearer ${token}`;
//   }
//   return config;
// });

// Add a response interceptor to handle errors globally
// api.interceptors.response.use(
//   (response) => response,
//   (error) => {
//     console.error('API Error:', error);
//     return Promise.reject(error);
//   }
// );

//Common API functions

//You need to be able to handle the user information in the context.  
//These functions require the user id.  You can get this from Clerk/Auth.js and pass it to the API functions as needed.
//Set up clerk/auth.js to provide user context throughout the app, and then use that context to get the user ID when calling these API functions.
export const graphApi = {
    getUserGraph: async () => {
        const response = await api.get('/graph/user-graph'); //TODO - confirm endpoint
        return response.data;
    },

    // getCourseSubGraph: async (courseId: string, userId: string) => {
    //     const response = await api.get(`/course-subgraph?courseId=${courseId}&userId=${userId}`);
    //     return response.data;
    // }
}

export const courseApi = {
    createCourse: async (topic: string) => {
        const response = await api.post('/courses', { topic });
        return response.data;
    },

    getUserCourses: async (userId: string) => {
        const response = await api.get(`/users/${userId}/courses`);
        return response.data;
    }
}

export const crewApi = {
    kickoffCrew: async (topic: string) => {
        console.log('kickoffCrew called with topic:', topic);
        const response = await api.get(`/crew/kickoff?topic=${encodeURIComponent(topic)}`);
        console.log('kickoffCrew response:', response.data);
        return response.data;
    }
}
export default api;