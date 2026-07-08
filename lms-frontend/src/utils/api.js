// Re-export everything from the new modular API structure
// This file is kept for backward compatibility

import apiClient, { getApiBaseUrl, uploadWithProgress } from "./apiClient";
import authApi from "./authApi";
import studentApi from "./studentApi";
import facultyApi from "./facultyApi";

// Export authAPI as the same name for backward compatibility
export const authAPI = authApi;

// Export other APIs
export { authApi, studentApi, facultyApi, getApiBaseUrl, uploadWithProgress };

// Export API client as default for custom requests
export default apiClient;
