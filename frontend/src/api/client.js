// src/api/client.js
import axios from "axios";

const AUTH_STORAGE_KEYS = {
  token: "bhashabot_token",
  username: "bhashabot_username",
  email: "bhashabot_email",
};

const getAuthStorage = () => sessionStorage;

const clearAuthStorage = () => {
  const storage = getAuthStorage();
  storage.removeItem(AUTH_STORAGE_KEYS.token);
  storage.removeItem(AUTH_STORAGE_KEYS.username);
  storage.removeItem(AUTH_STORAGE_KEYS.email);
};

const apiClient = axios.create({
  baseURL: "",  // Empty = use React proxy (package.json → http://localhost:8000)
  headers: { "Content-Type": "application/json" },
  timeout: 120000,
});

apiClient.interceptors.request.use(
  (config) => {
    const token = getAuthStorage().getItem(AUTH_STORAGE_KEYS.token);
    if (token) {
      config.headers["Authorization"] = `Bearer ${token}`;
    }
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
    if (error.response?.status === 401) {
      clearAuthStorage();
    }
    const message = error.response?.data?.detail || error.message || "An unexpected error occurred";
    return Promise.reject(new Error(message));
  }
);

export default apiClient;

// ── Auth API Calls ───────────────────────────────────────────────────────────

export const loginUser = async (username, password) => {
  const response = await apiClient.post("/api/login", { username, password });
  if (response.data?.access_token) {
    const storage = sessionStorage;
    storage.setItem("bhashabot_token", response.data.access_token);
    storage.setItem("bhashabot_username", response.data.username);
    storage.setItem("bhashabot_email", response.data.email);
  }
  return response.data;
};

export const signupUser = async (username, email, password, confirmPassword) => {
  const response = await apiClient.post("/api/signup", { 
    username,
    email, 
    password, 
    confirm_password: confirmPassword 
  });
  return response.data;
};

export const logoutUser = () => {
  clearAuthStorage();
};


export const checkCurrentUser = async () => {
  const response = await apiClient.get("/api/me");
  return response.data;
};

// ── Document and Chat API Calls ──────────────────────────────────────────────

export const getUserSessions = async () => {
  const response = await apiClient.get("/api/sessions");
  return response.data;
};

export const deleteUserSession = async (sessionId) => {
  const response = await apiClient.delete(`/api/sessions/${sessionId}`);
  return response.data;
};

export const uploadPDF = async (file, { sessionId = null, forceReprocess = false } = {}) => {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("force_reprocess", String(forceReprocess));
  if (sessionId) formData.append("session_id", sessionId);
  const response = await apiClient.post("/api/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
};

export const sendChatMessage = async (
  query,
  sessionId,
  history = [],
  preferredLanguage = "Auto Detect",
  tone = "Friendly"
) => {
  const response = await apiClient.post("/api/chat", {
    query,
    session_id: sessionId,
    history,
    preferred_language: preferredLanguage,
    tone,
  });
  return response.data;
};

