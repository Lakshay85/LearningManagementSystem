import { useState, useEffect, useCallback, createContext, useContext } from "react";
import { useNavigate } from "react-router-dom";
import authApi from "../utils/authApi";

// Create Auth Context
const AuthContext = createContext(null);

/**
 * Auth Provider Component
 * Wraps the app and provides authentication state and methods
 */
export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const navigate = useNavigate();

    // Fetch current user on mount
    const fetchCurrentUser = useCallback(async () => {
        try {
            setIsLoading(true);
            const userData = await authApi.getCurrentUser();
            setUser(userData);
            setIsAuthenticated(true);
        } catch (error) {
            // User not authenticated or session expired
            setUser(null);
            setIsAuthenticated(false);
        } finally {
            setIsLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchCurrentUser();
    }, [fetchCurrentUser]);

    /**
     * Logout the current user
     */
    const logout = useCallback(async () => {
        try {
            await authApi.logout();
        } catch (error) {
            // Even if logout API fails, clear local state
            console.error("Logout error:", error);
        } finally {
            setUser(null);
            setIsAuthenticated(false);
            navigate("/login");
        }
    }, [navigate]);

    /**
     * Refresh user data after a successful login
     */
    const refreshUser = useCallback(async () => {
        await fetchCurrentUser();
    }, [fetchCurrentUser]);

    /**
     * Get dashboard path based on user role
     */
    const getDashboardPath = useCallback(() => {
        if (!user) return "/login";
        const role = user.role;
        if (role === "teacher" || role === "faculty") {
            return "/faculty/dashboard";
        }
        return "/dashboard";
    }, [user]);

    const value = {
        user,
        isLoading,
        isAuthenticated,
        logout,
        refreshUser,
        getDashboardPath,
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

/**
 * Hook to access authentication context
 */
export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error("useAuth must be used within an AuthProvider");
    }
    return context;
};

export default useAuth;
