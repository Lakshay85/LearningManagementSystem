import apiClient from "./apiClient";

/**
 * Authentication API calls
 */
const authApi = {
  /**
   * Student signup
   * @param {object} userData - User registration data
   * @param {string} userData.email - User email
   * @param {string} userData.password - User password
   * @param {string} userData.firstName - User first name
   * @param {string} userData.lastName - User last name
   * @returns {Promise} - The response with user data
   */
  signup: async (userData) => {
    return await apiClient("/auth/student/signup", {
      method: "POST",
      data: {
        email: userData.email,
        password: userData.password,
        firstName: userData.firstName,
        lastName: userData.lastName,
      },
    });
  },

  /**
   * Faculty signup
   * @param {object} userData - Faculty registration data
   * @param {string} userData.email - Faculty email
   * @param {string} userData.password - Faculty password
   * @param {string} userData.firstName - Faculty first name
   * @param {string} userData.lastName - Faculty last name
   * @param {string} userData.department - Faculty department
   * @param {string} userData.specialization - Faculty specialization
   * @param {string} userData.qualification - Faculty qualification
   * @returns {Promise} - The response with user data
   */
  facultySignup: async (userData) => {
    return await apiClient("/auth/faculty/signup", {
      method: "POST",
      data: {
        email: userData.email,
        password: userData.password,
        firstName: userData.firstName,
        lastName: userData.lastName,
        department: userData.department,
        specialization: userData.specialization,
        qualification: userData.qualification,
      },
    });
  },

  /**
   * Unified login for all roles
   * @param {object} credentials - Login credentials
   * @param {string} credentials.email - User email
   * @param {string} credentials.password - User password
   * @returns {Promise} - The response with user data and tokens
   */
  login: async (credentials) => {
    return await apiClient("/auth/login", {
      method: "POST",
      data: {
        email: credentials.email,
        password: credentials.password,
      },
    });
  },

  /**
   * Refresh authentication token
   * @returns {Promise} - The response with new tokens
   */
  refreshToken: async () => {
    return await apiClient("/auth/refresh", {
      method: "POST",
    });
  },

  /**
   * Logout user
   * @returns {Promise} - The response confirming logout
   */
  logout: async () => {
    return await apiClient("/auth/logout", {
      method: "POST",
    });
  },

  /**
   * Get current authenticated user
   * @returns {Promise} - The response with user data
   */
  getCurrentUser: async () => {
    return await apiClient("/auth/me", {
      method: "GET",
      _suppressRedirect: true,
    });
  },

  /**
   * Get current user profile
   * @returns {Promise} - The response with user profile data
   */
  getProfile: async () => {
    return await apiClient("/auth/profile", {
      method: "GET",
    });
  },

  /**
   * Update user password
   * @param {object} passwordData - Password update data
   * @param {string} passwordData.currentPassword - Current password
   * @param {string} passwordData.newPassword - New password
   * @returns {Promise} - The response confirming password update
   */
  updatePassword: async (passwordData) => {
    return await apiClient("/auth/update-password", {
      method: "PUT",
      data: passwordData,
    });
  },

  /**
   * Delete user account
   * @returns {Promise} - The response confirming account deletion
   */
  deleteAccount: async () => {
    return await apiClient("/auth/delete-account", {
      method: "DELETE",
    });
  },
};

export default authApi;
