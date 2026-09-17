import apiClient from "./apiClient";

/**
 * Admin API wrapper for LMS administrative subsystem
 */
const adminApi = {
  // --- Dashboard ---
  getDashboardStats: async () => {
    return await apiClient("/admin/dashboard/stats", { method: "GET" });
  },

  // --- Users ---
  getUsers: async (params = {}) => {
    const query = new URLSearchParams();
    if (params.search) query.set("search", params.search);
    if (params.role) query.set("role", params.role);
    if (params.status) query.set("status", params.status);
    if (params.page) query.set("page", params.page);
    if (params.limit) query.set("limit", params.limit);
    const qs = query.toString() ? `?${query.toString()}` : "";
    return await apiClient(`/admin/users${qs}`, { method: "GET" });
  },

  getUser: async (userId) => {
    return await apiClient(`/admin/users/${userId}`, { method: "GET" });
  },

  createUser: async (userData) => {
    return await apiClient("/admin/users", {
      method: "POST",
      data: userData,
    });
  },

  updateUserStatus: async (userId, isActive) => {
    return await apiClient(`/admin/users/${userId}/status`, {
      method: "PATCH",
      data: { isActive },
    });
  },

  updateUserRole: async (userId, role) => {
    return await apiClient(`/admin/users/${userId}/role`, {
      method: "PATCH",
      data: { role },
    });
  },

  setUserLLMLimits: async (userId, { llmDailyLimit, llmMonthlyLimit }) => {
    return await apiClient(`/admin/users/${userId}/llm-limits`, {
      method: "PATCH",
      data: { llmDailyLimit, llmMonthlyLimit },
    });
  },

  resetUserPassword: async (userId, newPassword) => {
    return await apiClient(`/admin/users/${userId}/reset-password`, {
      method: "POST",
      data: { newPassword },
    });
  },

  deleteUser: async (userId) => {
    return await apiClient(`/admin/users/${userId}`, {
      method: "DELETE",
    });
  },

  updateAdminPermissions: async (userId, permissions) => {
    return await apiClient(`/admin/users/${userId}/permissions`, {
      method: "PATCH",
      data: { permissions },
    });
  },

  // --- Course Oversight ---
  getCourses: async (params = {}) => {
    const query = new URLSearchParams();
    if (params.search) query.set("search", params.search);
    if (params.status) query.set("status", params.status);
    if (params.page) query.set("page", params.page);
    if (params.limit) query.set("limit", params.limit);
    const qs = query.toString() ? `?${query.toString()}` : "";
    return await apiClient(`/admin/courses${qs}`, { method: "GET" });
  },

  unpublishCourse: async (courseId) => {
    return await apiClient(`/admin/courses/${courseId}/unpublish`, {
      method: "POST",
    });
  },

  // --- Content Oversight ---
  getDocuments: async (params = {}) => {
    const query = new URLSearchParams();
    if (params.search) query.set("search", params.search);
    if (params.page) query.set("page", params.page);
    if (params.limit) query.set("limit", params.limit);
    const qs = query.toString() ? `?${query.toString()}` : "";
    return await apiClient(`/admin/content/documents${qs}`, { method: "GET" });
  },

  removeDocument: async (documentId) => {
    return await apiClient(`/admin/content/documents/${documentId}`, {
      method: "DELETE",
    });
  },

  getVideos: async (params = {}) => {
    const query = new URLSearchParams();
    if (params.search) query.set("search", params.search);
    if (params.page) query.set("page", params.page);
    if (params.limit) query.set("limit", params.limit);
    const qs = query.toString() ? `?${query.toString()}` : "";
    return await apiClient(`/admin/content/videos${qs}`, { method: "GET" });
  },

  removeVideo: async (videoId) => {
    return await apiClient(`/admin/content/videos/${videoId}`, {
      method: "DELETE",
    });
  },

  // --- Quiz Oversight ---
  getQuizzes: async (params = {}) => {
    const query = new URLSearchParams();
    if (params.search) query.set("search", params.search);
    if (params.status) query.set("status", params.status);
    if (params.page) query.set("page", params.page);
    if (params.limit) query.set("limit", params.limit);
    const qs = query.toString() ? `?${query.toString()}` : "";
    return await apiClient(`/admin/quizzes${qs}`, { method: "GET" });
  },

  archiveQuiz: async (quizId) => {
    return await apiClient(`/admin/quizzes/${quizId}/archive`, {
      method: "POST",
    });
  },

  // --- LLM Usage Analytics ---
  getLLMUsageOverview: async () => {
    return await apiClient("/admin/llm/usage", { method: "GET" });
  },

  getUserLLMUsage: async (userId) => {
    return await apiClient(`/admin/llm/usage/${userId}`, { method: "GET" });
  },

  // --- Audit Logs ---
  getAuditLogs: async (params = {}) => {
    const query = new URLSearchParams();
    if (params.action) query.set("action", params.action);
    if (params.targetType) query.set("targetType", params.targetType);
    if (params.actorId) query.set("actorId", params.actorId);
    if (params.page) query.set("page", params.page);
    if (params.limit) query.set("limit", params.limit);
    const qs = query.toString() ? `?${query.toString()}` : "";
    return await apiClient(`/admin/audit-logs${qs}`, { method: "GET" });
  },

  // --- System Settings ---
  getSettings: async () => {
    return await apiClient("/admin/settings", { method: "GET" });
  },

  updateSetting: async (key, value, description) => {
    return await apiClient(`/admin/settings/${key}`, {
      method: "PATCH",
      data: { value, description },
    });
  },
};

export default adminApi;
