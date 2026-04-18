import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000",
  headers: {
    "Content-Type": "application/json"
  }
});

api.interceptors.request.use((config) => {
  const selectedUser = window.localStorage.getItem("ubid.demo-user") ?? "analyst.demo";
  const roleMap: Record<string, string> = {
    "viewer.demo": "viewer",
    "analyst.demo": "analyst",
    "admin.demo": "admin"
  };
  config.headers["X-Demo-User"] = selectedUser;
  config.headers["X-User-Role"] = roleMap[selectedUser] ?? "analyst";
  return config;
});

export default api;
