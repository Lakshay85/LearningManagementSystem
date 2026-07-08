import apiClient from "./apiClient";

/**
 * Notification API calls
 */
const notificationApi = {
    /**
     * Get all notifications for the current user
     * @param {object} params - Query parameters
     * @param {number} params.page - Page number
     * @param {number} params.limit - Items per page
     * @param {boolean} params.unreadOnly - Filter for unread only
     * @param {string} params.type - Filter by notification type
     * @returns {Promise} - Paginated notifications
     */
    getNotifications: async (params = {}) => {
        return await apiClient("/notifications", {
            method: "GET",
            params,
        });
    },

    /**
     * Get unread notification count
     * @returns {Promise} - { unreadCount: number }
     */
    getUnreadCount: async () => {
        return await apiClient("/notifications/unread-count", {
            method: "GET",
        });
    },

    /**
     * Mark a notification as read
     * @param {string} notificationId - Notification ID
     * @returns {Promise} - Updated notification
     */
    markAsRead: async (notificationId) => {
        return await apiClient(`/notifications/${notificationId}/read`, {
            method: "PATCH",
        });
    },

    /**
     * Mark all notifications as read
     * @returns {Promise} - { updated: number }
     */
    markAllAsRead: async () => {
        return await apiClient("/notifications/read-all", {
            method: "PATCH",
        });
    },

    /**
     * Delete a notification
     * @param {string} notificationId - Notification ID
     * @returns {Promise} - void
     */
    deleteNotification: async (notificationId) => {
        return await apiClient(`/notifications/${notificationId}`, {
            method: "DELETE",
        });
    },

    /**
     * Delete all notifications
     * @returns {Promise} - { deleted: number }
     */
    deleteAllNotifications: async () => {
        return await apiClient("/notifications", {
            method: "DELETE",
        });
    },

    /**
     * Get notification preferences
     * @returns {Promise} - Notification preferences
     */
    getPreferences: async () => {
        return await apiClient("/notifications/preferences", {
            method: "GET",
        });
    },

    /**
     * Update notification preferences
     * @param {object} preferences - Preference updates
     * @returns {Promise} - Updated preferences
     */
    updatePreferences: async (preferences) => {
        return await apiClient("/notifications/preferences", {
            method: "PATCH",
            data: preferences,
        });
    },

    /**
     * Create an EventSource connection for SSE notifications
     * @param {string} baseUrl - API base URL (from env or config)
     * @returns {EventSource} - SSE connection
     */
    createSSEConnection: (baseUrl) => {
        const sseUrl = `${baseUrl}/notifications/sse`;
        return new EventSource(sseUrl, { withCredentials: true });
    },
};

export default notificationApi;
