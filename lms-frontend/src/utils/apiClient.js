import axios from "axios";

// Get API base URL from environment variables
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:3000";

// Create axios instance with default configuration
const axiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true, // Include cookies for httpOnly tokens
});

// Flag to prevent multiple refresh attempts
let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, success = false) => {
  failedQueue.forEach((prom) => {
    if (success) {
      prom.resolve();
    } else {
      prom.reject(error);
    }
  });
  failedQueue = [];
};

// Request interceptor
axiosInstance.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor with token refresh logic
axiosInstance.interceptors.response.use(
  (response) => {
    return response.data;
  },
  async (error) => {
    const originalRequest = error.config;

    // Handle 401 errors with token refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      // Don't retry these auth endpoints to prevent infinite loops
      if (originalRequest.url?.includes("/auth/refresh") ||
        originalRequest.url?.includes("/auth/login") ||
        originalRequest.url?.includes("/auth/signup")) {
        return Promise.reject(createErrorResponse(error));
      }

      if (isRefreshing) {
        // Queue requests while refresh is in progress
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then(() => axiosInstance(originalRequest))
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        // Attempt to refresh the token
        await axiosInstance.post("/auth/refresh", {});
        processQueue(null, true);
        // Retry the original request
        return axiosInstance(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, false);
        // Refresh failed - redirect to login unless suppressed
        if (!originalRequest._suppressRedirect) {
          handleAuthFailure();
        }
        return Promise.reject(createErrorResponse(refreshError));
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(createErrorResponse(error));
  }
);

/**
 * Create standardized error response
 */
const createErrorResponse = (error) => ({
  status: error.response?.status || 500,
  message: error.response?.data?.message || "An error occurred",
  errors: error.response?.data?.errors || [],
});

/**
 * Handle authentication failure - clear state and redirect to login
 */
const handleAuthFailure = () => {
  // Only redirect if not already on login page
  if (!window.location.pathname.includes("/login")) {
    window.location.href = "/login";
  }
};

/**
 * API client for making HTTP requests
 */
const apiClient = async (endpoint, options = {}) => {
  const { method = "GET", data, params, headers, ...rest } = options;

  try {
    const response = await axiosInstance({
      url: endpoint,
      method,
      data,
      params,
      headers,
      ...rest,
    });

    return response;
  } catch (error) {
    throw error;
  }
};

/**
 * Upload file with progress tracking
 */
export const uploadWithProgress = async (endpoint, formData, onProgress, signal) => {
  try {
    const response = await axiosInstance({
      url: endpoint,
      method: "POST",
      data: formData,
      headers: {
        "Content-Type": "multipart/form-data",
      },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.lengthComputable && onProgress) {
          const progress = Math.round((progressEvent.loaded / progressEvent.total) * 100);
          onProgress(progress);
        }
      },
      signal,
    });

    return response;
  } catch (error) {
    if (axios.isCancel(error)) {
      throw { status: 0, message: "Upload cancelled", errors: [] };
    }
    throw error;
  }
};

// Export the API base URL for components that need it directly
export const getApiBaseUrl = () => API_BASE_URL;

// Export axios instance for advanced usage
export { axiosInstance };

// Export API client as default
export default apiClient;
