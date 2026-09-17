import apiClient, { uploadWithProgress, getApiBaseUrl } from "./apiClient";

/**
 * Faculty API calls
 */
const facultyApi = {
  /**
   * Get faculty dashboard data
   * @returns {Promise} - Dashboard statistics and overview
   */
  getDashboard: async () => {
    return await apiClient("/faculty/dashboard", {
      method: "GET",
    });
  },

  /**
   * Get faculty profile
   * @returns {Promise} - Faculty profile data
   */
  getProfile: async () => {
    return await apiClient("/faculty/profile", {
      method: "GET",
    });
  },

  /**
   * Update faculty profile
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
   * Upload profile picture
   * @param {FormData} formData - Form data with file
   * @returns {Promise} - Response with new profile picture URL
   */
  uploadProfilePicture: async (formData) => {
    return await apiClient("/users/upload-profile-picture", {
      method: "POST",
      data: formData,
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
  },

  /**
   * Update password
   * @param {object} passwordData - Current and new password
   * @returns {Promise} - Success message
   */
  updatePassword: async (passwordData) => {
    return await apiClient("/auth/update-password", {
      method: "PUT",
      data: passwordData,
    });
  },

  /**
   * Delete account
   * @returns {Promise} - Success message
   */
  deleteAccount: async () => {
    return await apiClient("/auth/delete-account", {
      method: "DELETE",
    });
  },

  // ============ Video Management ============

  /**
   * Get recent videos uploaded by the current faculty
   * @param {number} limit - Number of recent videos to fetch (default: 5)
   * @returns {Promise} - List of recent videos
   */
  getMyRecentVideos: async (limit = 5) => {
    return await apiClient("/videos/my-recent", {
      method: "GET",
      params: { limit },
    });
  },

  /**
   * Get faculty video statistics
   * @returns {Promise} - Video statistics (total videos, views, growth, etc.)
   */
  getMyVideoStats: async () => {
    return await apiClient("/videos/my-stats", {
      method: "GET",
    });
  },

  /**
   * Get faculty's videos
   * @param {object} params - Query parameters
   * @param {number} params.page - Page number
   * @param {number} params.limit - Items per page
   * @param {string} params.search - Search query
   * @param {string} params.category - Category filter
   * @param {string} params.visibility - Visibility filter
   * @returns {Promise} - List of videos with pagination
   */
  getMyVideos: async (params = {}) => {
    return await apiClient("/videos/my-videos", {
      method: "GET",
      params,
    });
  },

  /**
   * Get all content (videos + documents)
   * @param {object} params - Query parameters
   * @param {number} params.page - Page number
   * @param {number} params.limit - Items per page
   * @param {string} params.search - Search query
   * @param {string} params.fileType - File type filter (video, pdf, word, excel, etc.)
   * @param {string} params.timeRange - Time range filter (today, week, month, quarter, year)
   * @param {string} params.sizeRange - Size range filter (small, medium, large, xlarge)
   * @param {string} params.sortBy - Sort option (newest, oldest, title, size-desc, size-asc, popular)
   * @returns {Promise} - List of all content with pagination
   */
  getAllContent: async (params = {}) => {
    return await apiClient("/faculty/all-content", {
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
   * Upload a new video
   * @param {FormData} formData - Form data containing video file and metadata
   * @param {function} onProgress - Progress callback (receives percentage 0-100)
   * @param {AbortSignal} signal - Optional abort signal for cancellation
   * @returns {Promise} - Upload response with video data
   */
  uploadVideo: async (formData, onProgress, signal) => {
    return await uploadWithProgress(
      "/videos/upload",
      formData,
      onProgress,
      signal
    );
  },

  /**
   * Update video metadata
   * @param {string} videoId - Video ID
   * @param {object} updateData - Data to update
   * @param {string} updateData.title - Video title
   * @param {string} updateData.description - Video description
   * @param {string} updateData.category - Video category
   * @param {string} updateData.visibility - Video visibility
   * @returns {Promise} - Updated video data
   */
  updateVideo: async (videoId, updateData) => {
    return await apiClient(`/videos/${videoId}`, {
      method: "PUT",
      data: updateData,
    });
  },

  /**
   * Delete a video
   * @param {string} videoId - Video ID
   * @returns {Promise} - Deletion confirmation
   */
  deleteVideo: async (videoId) => {
    return await apiClient(`/videos/${videoId}`, {
      method: "DELETE",
    });
  },

  /**
   * Get video streaming URL
   * @param {string} videoId - Video ID
   * @returns {string} - Full streaming URL
   */
  getVideoStreamUrl: (videoId) => {
    return `${getApiBaseUrl()}/videos/stream/${videoId}`;
  },

  /**
   * Update video visibility
   * @param {string} videoId - Video ID
   * @param {string} visibility - New visibility (public, private, unlisted)
   * @returns {Promise} - Updated video data
   */
  updateVideoVisibility: async (videoId, visibility) => {
    return await apiClient(`/videos/${videoId}/visibility`, {
      method: "PATCH",
      data: { visibility },
    });
  },

  /**
   * Get faculty's documents
   * @param {object} params - Query parameters
   * @returns {Promise} - List of documents
   */
  getMyDocuments: async (params = {}) => {
    return await apiClient("/documents/my-documents", {
      method: "GET",
      params,
    });
  },

  // ============ Course Management ============

  /**
   * Get faculty's courses
   * @param {object} params - Query parameters
   * @returns {Promise} - List of courses
   */
  getMyCourses: async (params = {}) => {
    return await apiClient("/courses/my-courses", {
      method: "GET",
      params,
    });
  },

  /**
   * Get recent courses for dashboard
   * @param {number} limit - Number of recent courses to fetch
   * @returns {Promise} - List of recent courses
   */
  getMyRecentCourses: async (limit = 5) => {
    return await apiClient("/courses/my-recent", {
      method: "GET",
      params: { limit },
    });
  },

  /**
   * Get course statistics
   * @returns {Promise} - Course statistics
   */
  getMyCourseStats: async () => {
    return await apiClient("/courses/my-stats", {
      method: "GET",
    });
  },

  /**
   * Create a new course
   * @param {object} courseData - Course data
   * @returns {Promise} - Created course
   */
  createCourse: async (courseData) => {
    return await apiClient("/courses", {
      method: "POST",
      data: courseData,
    });
  },

  /**
   * Get course by ID
   * @param {string} courseId - Course ID
   * @returns {Promise} - Course details
   */
  getCourseById: async (courseId) => {
    return await apiClient(`/courses/${courseId}`, {
      method: "GET",
    });
  },

  /**
   * Update a course
   * @param {string} courseId - Course ID
   * @param {object} updateData - Data to update
   * @returns {Promise} - Updated course
   */
  updateCourse: async (courseId, updateData) => {
    return await apiClient(`/courses/${courseId}`, {
      method: "PATCH",
      data: updateData,
    });
  },

  /**
   * Delete a course
   * @param {string} courseId - Course ID
   * @returns {Promise} - Deletion confirmation
   */
  deleteCourse: async (courseId) => {
    return await apiClient(`/courses/${courseId}`, {
      method: "DELETE",
    });
  },

  /**
   * Get faculty's students
   * @returns {Promise} - List of students enrolled in faculty's courses
   */
  getFacultyStudents: async () => {
    return await apiClient("/courses/faculty/students", {
      method: "GET",
    });
  },


  // ============ Section Management ============

  /**
   * Add section to course
   * @param {string} courseId - Course ID
   * @param {object} sectionData - Section data (title, description, order)
   * @returns {Promise} - Created section
   */
  addSection: async (courseId, sectionData) => {
    return await apiClient(`/courses/${courseId}/sections`, {
      method: "POST",
      data: sectionData,
    });
  },

  /**
   * Update section
   * @param {string} sectionId - Section ID
   * @param {object} updateData - Data to update
   * @returns {Promise} - Updated section
   */
  updateSection: async (sectionId, updateData) => {
    return await apiClient(`/courses/sections/${sectionId}`, {
      method: "PATCH",
      data: updateData,
    });
  },

  /**
   * Delete section
   * @param {string} sectionId - Section ID
   * @returns {Promise} - Deletion confirmation
   */
  deleteSection: async (sectionId) => {
    return await apiClient(`/courses/sections/${sectionId}`, {
      method: "DELETE",
    });
  },

  // ============ Content Management ============

  /**
   * Add content to section
   * @param {string} sectionId - Section ID
   * @param {object} contentData - Content data
   * @returns {Promise} - Created content
   */
  addContent: async (sectionId, contentData) => {
    return await apiClient(`/courses/sections/${sectionId}/content`, {
      method: "POST",
      data: contentData,
    });
  },

  /**
   * Upload document to section
   * @param {string} sectionId - Section ID
   * @param {FormData} formData - Form data containing document and title
   * @param {function} onProgress - Progress callback
   * @param {AbortSignal} signal - Optional abort signal
   * @returns {Promise} - Created content with document
   */
  uploadDocument: async (sectionId, formData, onProgress, signal) => {
    return await uploadWithProgress(
      `/courses/sections/${sectionId}/document`,
      formData,
      onProgress,
      signal
    );
  },

  /**
   * Upload multiple documents to section
   * @param {string} sectionId - Section ID
   * @param {FormData} formData - Form data containing documents
   * @param {function} onProgress - Progress callback
   * @param {AbortSignal} signal - Optional abort signal
   * @returns {Promise} - Upload results
   */
  uploadMultipleDocuments: async (sectionId, formData, onProgress, signal) => {
    return await uploadWithProgress(
      `/courses/sections/${sectionId}/documents`,
      formData,
      onProgress,
      signal
    );
  },

  /**
   * Update document
   * @param {string} documentId - Document ID
   * @param {object} updateData - Data to update (e.g. visibility)
   * @returns {Promise} - Updated document
   */
  updateDocument: async (documentId, updateData) => {
    return await apiClient(`/documents/${documentId}`, {
      method: "PATCH",
      data: updateData,
    });
  },

  /**
   * Delete content
   * @param {string} contentId - Content ID
   * @returns {Promise} - Deletion confirmation
   */
  deleteContent: async (contentId) => {
    return await apiClient(`/courses/content/${contentId}`, {
      method: "DELETE",
    });
  },

  /**
   * Get document download URL
   * @param {string} documentId - Document ID
   * @returns {string} - Full download URL
   */
  getDocumentDownloadUrl: (documentId) => {
    return `${getApiBaseUrl()}/courses/documents/${documentId}/download`;
  },

  getMyDocuments: async (params = {}) => {
    return await apiClient("/documents/my-documents", {
      method: "GET",
      params,
    });
  },

  // ============ Analytics ============

  /**
   * Get video analytics
   * @param {string} videoId - Video ID (optional, for specific video)
   * @param {object} params - Query parameters
   * @returns {Promise} - Analytics data
   */
  getVideoAnalytics: async (videoId = null, params = {}) => {
    const endpoint = videoId
      ? `/faculty/analytics/videos/${videoId}`
      : "/faculty/analytics/videos";
    return await apiClient(endpoint, {
      method: "GET",
      params,
    });
  },

  /**
   * Get course analytics
   * @param {string} courseId - Course ID (optional)
   * @param {object} params - Query parameters
   * @returns {Promise} - Analytics data
   */
  getCourseAnalytics: async (courseId = null, params = {}) => {
    const endpoint = courseId
      ? `/faculty/analytics/courses/${courseId}`
      : "/faculty/analytics/courses";
    return await apiClient(endpoint, {
      method: "GET",
      params,
    });
  },

  /**
   * Get student engagement statistics
   * @param {object} params - Query parameters
   * @returns {Promise} - Engagement data
   */
  getStudentEngagement: async (params = {}) => {
    return await apiClient("/faculty/analytics/engagement", {
      method: "GET",
      params,
    });
  },

  /**
   * Get detailed video analytics (published vs draft)
   * @returns {Promise} - Detailed video analytics
   */
  getVideoAnalyticsDetails: async () => {
    return await apiClient("/videos/analytics/details", {
      method: "GET",
    });
  },

  /**
   * Get detailed course analytics (published vs draft)
   * @returns {Promise} - Detailed course analytics
   */
  getCourseAnalyticsDetails: async () => {
    return await apiClient("/courses/analytics/details", {
      method: "GET",
    });
  },

  // ============ Quiz Management ============
  createQuiz: async (data) => {
    return await apiClient("/quizzes", {
      method: "POST",
      data,
    });
  },

  generateQuizWithAI: async (data) => {
    return await apiClient("/quizzes/generate", {
      method: "POST",
      data,
    });
  },

  getCourseQuizzes: async (courseId, params = {}) => {
    return await apiClient(`/quizzes/course/${courseId}`, {
      method: "GET",
      params,
    });
  },

  getQuiz: async (quizId) => {
    return await apiClient(`/quizzes/${quizId}`, {
      method: "GET",
    });
  },

  updateQuiz: async (quizId, data) => {
    return await apiClient(`/quizzes/${quizId}`, {
      method: "PATCH",
      data,
    });
  },

  publishQuiz: async (quizId) => {
    return await apiClient(`/quizzes/${quizId}/publish`, {
      method: "POST",
    });
  },

  archiveQuiz: async (quizId) => {
    return await apiClient(`/quizzes/${quizId}/archive`, {
      method: "POST",
    });
  },

  deleteQuiz: async (quizId) => {
    return await apiClient(`/quizzes/${quizId}`, {
      method: "DELETE",
    });
  },

  addQuestion: async (quizId, data) => {
    return await apiClient(`/quizzes/${quizId}/questions`, {
      method: "POST",
      data,
    });
  },

  updateQuestion: async (questionId, data) => {
    return await apiClient(`/quizzes/questions/${questionId}`, {
      method: "PATCH",
      data,
    });
  },

  deleteQuestion: async (questionId) => {
    return await apiClient(`/quizzes/questions/${questionId}`, {
      method: "DELETE",
    });
  },

  getQuizSubmissions: async (quizId) => {
    return await apiClient(`/quizzes/${quizId}/submissions`, {
      method: "GET",
    });
  },
};


export default facultyApi;
