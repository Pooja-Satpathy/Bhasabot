// src/api/client.js
import axios from "axios";

const apiClient = axios.create({
  baseURL: process.env.REACT_APP_API_URL || "http://localhost:8000",
  headers: { "Content-Type": "application/json" },
  timeout: 120000,
});

apiClient.interceptors.request.use(
  (config) => {
    if (process.env.NODE_ENV === "development") {
      console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`);
    }
    return config;
  },
  (error) => Promise.reject(error)
);

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error.response?.data?.detail || error.message || "An unexpected error occurred";
    return Promise.reject(new Error(message));
  }
);

export default apiClient;

export const uploadPDF = async (file, sessionId = null) => {
  const formData = new FormData();
  formData.append("file", file);
  if (sessionId) formData.append("session_id", sessionId);
  const response = await apiClient.post("/api/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
};

export const sendChatMessage = async (query, sessionId) => {
  const response = await apiClient.post("/api/chat", { query, session_id: sessionId });
  return response.data;
};
