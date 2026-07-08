// Central export for all API utilities
export { default as apiClient, getApiBaseUrl, uploadWithProgress } from "./apiClient";
export { default as authApi } from "./authApi";
export { default as studentApi } from "./studentApi";
export { default as facultyApi } from "./facultyApi";

// Backward compatibility export
export { authAPI } from "./api";
