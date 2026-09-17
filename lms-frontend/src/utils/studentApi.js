import apiClient from "./apiClient";

/**
 * Student API calls
 */
const studentApi = {
  /**
   * Get student dashboard data
   * @returns {Promise} - Dashboard statistics and overview
   */
  getDashboard: async () => {
    return await apiClient("/students/dashboard", {
      method: "GET",
    });
  },

  /**
   * Get student profile
   * @returns {Promise} - Student profile data
   */
  getProfile: async () => {
    return await apiClient("/students/profile", {
      method: "GET",
    });
  },

  /**
   * Update student profile
   * @param {object} profileData - Profile data to update
   * @returns {Promise} - Updated profile data
   */
  updateProfile: async (profileData) => {
    return await apiClient("/auth/update-profile", {
      method: "PUT",
      data: profileData,
    });
  },

  /**
   * Get all available courses
   * @param {object} params - Query parameters
   * @param {number} params.page - Page number
   * @param {number} params.limit - Items per page
   * @param {string} params.search - Search query
   * @param {string} params.category - Category filter
   * @returns {Promise} - List of courses with pagination
   */
  getCourses: async (params = {}) => {
    return await apiClient("/courses", {
      method: "GET",
      params,
    });
  },

  /**
   * Get course details
   * @param {string} courseId - Course ID
   * @returns {Promise} - Course details
   */
  getCourseById: async (courseId) => {
    return await apiClient(`/courses/${courseId}`, {
      method: "GET",
    });
  },

  /**
   * Enroll in a course
   * @param {string} courseId - Course ID to enroll in
   * @returns {Promise} - Enrollment confirmation
   */
  enrollCourse: async (courseId) => {
    return await apiClient(`/courses/${courseId}/enroll`, {
      method: "POST",
    });
  },

  /**
   * Get enrolled courses
   * @param {object} params - Query parameters
   * @returns {Promise} - List of enrolled courses
   */
  getEnrolledCourses: async (params = {}) => {
    return await apiClient("/students/enrolled-courses", {
      method: "GET",
      params,
    });
  },

  /**
   * Get recommended videos
   * @param {object} params - Query parameters
   * @param {number} params.page - Page number
   * @param {number} params.limit - Items per page
   * @returns {Promise} - List of recommended videos
   */
  getRecommendedVideos: async (params = {}) => {
    return await apiClient("/videos/recommended", {
      method: "GET",
      params,
    });
  },

  /**
   * Get all videos
   * @param {object} params - Query parameters
   * @param {number} params.page - Page number
   * @param {number} params.limit - Items per page
   * @param {string} params.search - Search query
   * @param {string} params.category - Category filter
   * @returns {Promise} - List of videos with pagination
   */
  getVideos: async (params = {}) => {
    return await apiClient("/videos", {
      method: "GET",
      params,
    });
  },

  /**
   * Get video by ID
   * @param {string} videoId - Video ID
   * @returns {Promise} - Video details
   */
  getVideoById: async (videoId) => {
    return await apiClient(`/videos/${videoId}`, {
      method: "GET",
    });
  },

  /**
   * Track video progress
   * @param {string} videoId - Video ID
   * @param {object} progressData - Progress data
   * @param {number} progressData.watchedDuration - Duration watched in seconds
   * @param {number} progressData.totalDuration - Total video duration
   * @returns {Promise} - Updated progress
   */
  updateVideoProgress: async (videoId, progressData) => {
    return await apiClient(`/videos/${videoId}/progress`, {
      method: "POST",
      data: progressData,
    });
  },

  /**
   * Get student's watch history
   * @param {object} params - Query parameters
   * @returns {Promise} - List of watched videos
   */
  getWatchHistory: async (params = {}) => {
    return await apiClient("/students/watch-history", {
      method: "GET",
      params,
    });
  },

  /**
   * Get student's learning progress
   * @returns {Promise} - Learning progress statistics
   */
  getLearningProgress: async () => {
    return await apiClient("/students/progress", {
      method: "GET",
    });
  },

  /**
   * Add video to favorites
   * @param {string} videoId - Video ID
   * @returns {Promise} - Confirmation
   */
  addToFavorites: async (videoId) => {
    return await apiClient(`/students/favorites/${videoId}`, {
      method: "POST",
    });
  },

  /**
   * Remove video from favorites
   * @param {string} videoId - Video ID
   * @returns {Promise} - Confirmation
   */
  removeFromFavorites: async (videoId) => {
    return await apiClient(`/students/favorites/${videoId}`, {
      method: "DELETE",
    });
  },

  /**
   * Get favorite videos
   * @param {object} params - Query parameters
   * @returns {Promise} - List of favorite videos
   */
  getFavorites: async (params = {}) => {
    return await apiClient("/students/favorites", {
      method: "GET",
      params,
    });
  },

  /**
   * Get all published courses with pagination
   * @param {object} params - Query parameters
   * @param {number} params.page - Page number
   * @param {number} params.limit - Items per page
   * @param {string} params.search - Search query
   * @param {string} params.category - Category filter
   * @param {string} params.level - Level filter
   * @returns {Promise} - List of published courses with pagination
   */
  getPublishedCourses: async (params = {}) => {
    return await apiClient("/courses/published", {
      method: "GET",
      params,
    });
  },

  /**
   * Get course content summary (videos and documents count)
   * @param {string} courseId - Course ID
   * @returns {Promise} - Course content summary
   */
  getCourseContentSummary: async (courseId) => {
    return await apiClient(`/courses/${courseId}/content-summary`, {
      method: "GET",
    });
  },

  /**
   * Get public course details
   * @param {string} courseId - Course ID
   * @returns {Promise} - Course details
   */
  getPublicCourseById: async (courseId) => {
    return await apiClient(`/courses/public/${courseId}`, {
      method: "GET",
    });
  },

  /**
   * Enroll in a course
   * @param {string} courseId - Course ID to enroll in
   * @returns {Promise} - Enrollment confirmation
   */
  enrollInCourse: async (courseId) => {
    return await apiClient(`/courses/${courseId}/enroll`, {
      method: "POST",
    });
  },

  /**
   * Get all enrolled courses for the current student
   * @returns {Promise} - List of enrolled courses
   */
  getMyEnrolledCourses: async () => {
    return await apiClient("/courses/enrolled/my-courses", {
      method: "GET",
    });
  },

  /**
   * Get full course content for enrolled student
   * @param {string} courseId - Course ID
   * @returns {Promise} - Full course content with sections and materials
   */
  getEnrolledCourseContent: async (courseId) => {
    return await apiClient(`/courses/${courseId}/enrolled-content`, {
      method: "GET",
    });
  },

  /**
   * Check enrollment status for a course
   * @param {string} courseId - Course ID
   * @returns {Promise} - Enrollment status
   */
  getEnrollmentStatus: async (courseId) => {
    return await apiClient(`/courses/${courseId}/enrollment-status`, {
      method: "GET",
    });
  },

  /**
   * Update course progress
   * @param {string} courseId - Course ID
   * @param {number} progress - Progress percentage (0-100)
   * @returns {Promise} - Updated enrollment
   */
  updateCourseProgress: async (courseId, progress) => {
    return await apiClient(`/courses/${courseId}/progress`, {
      method: "PATCH",
      data: { progress },
    });
  },

  // ============ Quiz Student APIs ============
  getCourseQuizzes: async (courseId) => {
    return await apiClient(`/quizzes/course/${courseId}/published`, {
      method: "GET",
    });
  },

  getQuizForTaking: async (quizId) => {
    return await apiClient(`/quizzes/${quizId}/take`, {
      method: "GET",
    });
  },

  submitQuiz: async (quizId, answers) => {
    return await apiClient(`/quizzes/${quizId}/submit`, {
      method: "POST",
      data: { answers },
    });
  },

  getMyQuizResult: async (quizId) => {
    return await apiClient(`/quizzes/${quizId}/my-result`, {
      method: "GET",
    });
  },
};

export default studentApi;
