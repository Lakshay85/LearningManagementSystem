import { useState, useEffect, useCallback, useRef } from "react";
import { X, Bell, Info, CheckCircle, AlertTriangle, Clock, Loader2, RefreshCw } from "lucide-react";
import notificationApi from "../utils/notificationApi";
import { getApiBaseUrl } from "../utils/apiClient";

const NotificationSection = ({ isOpen, onClose }) => {
    const [notifications, setNotifications] = useState([]);
    const [unreadCount, setUnreadCount] = useState(0);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const eventSourceRef = useRef(null);

    // Fetch notifications from API
    const fetchNotifications = useCallback(async () => {
        if (!isOpen) return;

        try {
            setLoading(true);
            setError(null);
            const response = await notificationApi.getNotifications({ limit: 50 });
            setNotifications(response.data || []);
            setUnreadCount(response.unreadCount || 0);
        } catch (err) {
            console.error("Failed to fetch notifications:", err);
            setError("Failed to load notifications");
        } finally {
            setLoading(false);
        }
    }, [isOpen]);

    // Setup SSE connection for real-time updates
    useEffect(() => {
        if (isOpen && !eventSourceRef.current) {
            try {
                const baseUrl = getApiBaseUrl();
                const eventSource = notificationApi.createSSEConnection(baseUrl);

                eventSource.onmessage = (event) => {
                    try {
                        const data = JSON.parse(event.data);

                        if (data.type === 'new_notification') {
                            // Add new notification to the top of the list
                            setNotifications(prev => [data.notification, ...prev]);
                            setUnreadCount(data.unreadCount);
                        } else if (data.type === 'notification_read') {
                            // Update the read status
                            setNotifications(prev =>
                                prev.map(n => n.id === data.notification.id ? data.notification : n)
                            );
                            setUnreadCount(data.unreadCount);
                        } else if (data.type === 'all_read') {
                            // Mark all as read
                            setNotifications(prev =>
                                prev.map(n => ({ ...n, isRead: true, readAt: new Date().toISOString() }))
                            );
                            setUnreadCount(0);
                        }
                    } catch {
                        // Ignore heartbeat messages and parse errors
                    }
                };

                eventSource.onerror = () => {
                    // SSE connection error - will auto-reconnect
                    console.log("SSE connection error, will retry...");
                };

                eventSourceRef.current = eventSource;
            } catch (err) {
                console.error("Failed to setup SSE:", err);
            }
        }

        return () => {
            if (eventSourceRef.current) {
                eventSourceRef.current.close();
                eventSourceRef.current = null;
            }
        };
    }, [isOpen]);

    // Fetch notifications when panel opens
    useEffect(() => {
        if (isOpen) {
            fetchNotifications();
        }
    }, [isOpen, fetchNotifications]);

    const getIcon = (type) => {
        switch (type) {
            case "enrollment_success":
            case "course_published":
            case "video_uploaded":
                return <CheckCircle className="w-5 h-5 text-emerald-500" />;
            case "reminder":
                return <AlertTriangle className="w-5 h-5 text-amber-500" />;
            case "content_added":
            case "new_enrollment":
            case "info":
            default:
                return <Info className="w-5 h-5 text-blue-500" />;
        }
    };

    const formatTime = (dateString) => {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) return "Just now";
        if (diffMins < 60) return `${diffMins} min ago`;
        if (diffHours < 24) return `${diffHours} hr ago`;
        if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
        return date.toLocaleDateString();
    };

    const handleNotificationClick = async (notification) => {
        if (!notification.isRead) {
            try {
                await notificationApi.markAsRead(notification.id);
                setNotifications(prev =>
                    prev.map(n => n.id === notification.id ? { ...n, isRead: true, readAt: new Date().toISOString() } : n)
                );
                setUnreadCount(prev => Math.max(0, prev - 1));
            } catch (err) {
                console.error("Failed to mark as read:", err);
            }
        }
    };

    const markAllAsRead = async () => {
        try {
            await notificationApi.markAllAsRead();
            setNotifications(prev =>
                prev.map(n => ({ ...n, isRead: true, readAt: new Date().toISOString() }))
            );
            setUnreadCount(0);
        } catch (err) {
            console.error("Failed to mark all as read:", err);
        }
    };

    return (
        <>
            {/* Overlay */}
            {isOpen && (
                <div
                    className="fixed inset-0 bg-black/20 backdrop-blur-sm z-[60] transition-opacity"
                    onClick={onClose}
                />
            )}

            {/* Slide-in Panel */}
            <div
                className={`fixed top-0 right-0 h-full w-full max-w-sm bg-white shadow-2xl z-[70] transform transition-transform duration-500 ease-in-out flex flex-col ${isOpen ? "translate-x-0" : "translate-x-full"
                    }`}
            >
                {/* Header */}
                <div className="p-6 border-b border-slate-100 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="size-10 rounded-xl bg-indigo-50 flex items-center justify-center text-indigo-600">
                            <Bell className="w-5 h-5" />
                        </div>
                        <div>
                            <h2 className="text-xl font-bold text-slate-900">Notifications</h2>
                            <p className="text-xs text-slate-500 font-medium">
                                You have {unreadCount} unread alert{unreadCount !== 1 ? 's' : ''}
                            </p>
                        </div>
                    </div>
                    <div className="flex items-center gap-2">
                        <button
                            onClick={fetchNotifications}
                            className="p-2 hover:bg-slate-100 rounded-lg transition-colors text-slate-400 hover:text-slate-600"
                            title="Refresh"
                        >
                            <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
                        </button>
                        <button
                            onClick={onClose}
                            className="p-2 hover:bg-red-50 rounded-lg transition-colors text-slate-400 hover:text-red-500"
                        >
                            <X className="w-6 h-6" />
                        </button>
                    </div>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto no-scrollbar">
                    {loading && notifications.length === 0 ? (
                        <div className="h-full flex flex-col items-center justify-center p-12">
                            <Loader2 className="w-8 h-8 text-indigo-500 animate-spin mb-4" />
                            <p className="text-slate-500 text-sm">Loading notifications...</p>
                        </div>
                    ) : error ? (
                        <div className="h-full flex flex-col items-center justify-center p-12 text-center">
                            <div className="size-16 rounded-full bg-red-50 flex items-center justify-center mb-4">
                                <AlertTriangle className="w-8 h-8 text-red-400" />
                            </div>
                            <h3 className="text-lg font-bold text-slate-900 mb-1">Error</h3>
                            <p className="text-slate-500 text-sm">{error}</p>
                            <button
                                onClick={fetchNotifications}
                                className="mt-4 px-4 py-2 bg-indigo-500 text-white rounded-lg text-sm hover:bg-indigo-600 transition-colors"
                            >
                                Try Again
                            </button>
                        </div>
                    ) : notifications.length > 0 ? (
                        <div className="divide-y divide-slate-50">
                            {notifications.map((n) => (
                                <div
                                    key={n.id}
                                    onClick={() => handleNotificationClick(n)}
                                    className={`p-6 hover:bg-slate-50/50 transition-colors cursor-pointer relative group ${!n.isRead ? "bg-indigo-50/30" : ""
                                        }`}
                                >
                                    {!n.isRead && (
                                        <div className="absolute left-0 top-0 bottom-0 w-1 bg-indigo-500" />
                                    )}
                                    <div className="flex gap-4">
                                        <div className="mt-1">{getIcon(n.type)}</div>
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center justify-between mb-1">
                                                <h4 className="text-sm font-bold text-slate-900 truncate">
                                                    {n.title}
                                                </h4>
                                                <span className="text-[10px] font-bold text-slate-400 flex items-center gap-1 uppercase tracking-wider">
                                                    <Clock className="w-3 h-3" />
                                                    {formatTime(n.createdAt)}
                                                </span>
                                            </div>
                                            <p className="text-sm text-slate-600 leading-relaxed">
                                                {n.message}
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="h-full flex flex-col items-center justify-center p-12 text-center">
                            <div className="size-16 rounded-full bg-slate-50 flex items-center justify-center mb-4">
                                <Bell className="w-8 h-8 text-slate-300" />
                            </div>
                            <h3 className="text-lg font-bold text-slate-900 mb-1">All Caught Up!</h3>
                            <p className="text-slate-500 text-sm">No new notifications at the moment.</p>
                        </div>
                    )}
                </div>

                {/* Footer */}
                {notifications.length > 0 && (
                    <div className="p-6 border-t border-slate-100 bg-slate-50/50">
                        <button
                            onClick={markAllAsRead}
                            disabled={unreadCount === 0}
                            className="w-full py-3 bg-white border border-slate-200 text-slate-600 font-bold rounded-2xl hover:bg-white hover:border-indigo-500 hover:text-indigo-600 transition-all shadow-sm focus:outline-none focus:ring-0 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:border-slate-200 disabled:hover:text-slate-600"
                        >
                            Mark All as Read
                        </button>
                    </div>
                )}
            </div>
        </>
    );
};

export default NotificationSection;

