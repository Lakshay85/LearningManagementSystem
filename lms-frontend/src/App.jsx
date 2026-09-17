import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";
import { AuthProvider, useAuth } from "./hooks/useAuth";
import Login from "./components/Login";
import Signup from "./components/Signup";
import FacultySignup from "./components/FacultySignup";
import LandingPage from "./components/LandingPage";
import StudentDashboard from "./student/dashboard/StudentDashboard";
import FacultyDashboard from "./faculty/dashboard/FacultyDashboard";
import AdminDashboard from "./admin/dashboard/AdminDashboard";
import LmsLogo from "./components/common/LmsLogo";

/**
 * Loading component shown during auth check
 */
const LoadingScreen = () => (
  <div className="min-h-screen flex items-center justify-center bg-gray-50">
    <div className="flex flex-col items-center gap-4">
      <LmsLogo size={52} className="animate-pulse" />
      <div className="w-8 h-8 border-3 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
      <p className="text-gray-600 font-medium text-sm">Loading LMS Enterprise...</p>
    </div>
  </div>
);

/**
 * Protected route wrapper for students
 */
const StudentRoute = ({ children }) => {
  const { isAuthenticated, isLoading, user } = useAuth();

  if (isLoading) {
    return <LoadingScreen />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" />;
  }

  const role = user?.role;
  if (role === "admin") {
    return <Navigate to="/admin/dashboard" />;
  }
  if (role === "teacher" || role === "faculty") {
    return <Navigate to="/faculty/dashboard" />;
  }

  return children;
};

/**
 * Protected route wrapper for faculty
 */
const FacultyRoute = ({ children }) => {
  const { isAuthenticated, isLoading, user } = useAuth();

  if (isLoading) {
    return <LoadingScreen />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" />;
  }

  const role = user?.role;
  if (role === "admin") {
    return <Navigate to="/admin/dashboard" />;
  }
  if (role !== "teacher" && role !== "faculty") {
    return <Navigate to="/dashboard" />;
  }

  return children;
};

/**
 * Protected route wrapper for admins
 */
const AdminRoute = ({ children }) => {
  const { isAuthenticated, isLoading, user } = useAuth();

  if (isLoading) {
    return <LoadingScreen />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" />;
  }

  const role = user?.role;
  if (role !== "admin") {
    if (role === "teacher" || role === "faculty") {
      return <Navigate to="/faculty/dashboard" />;
    }
    return <Navigate to="/dashboard" />;
  }

  return children;
};

/**
 * Public route that redirects authenticated users to dashboard
 */
const PublicRoute = ({ children }) => {
  const { isAuthenticated, isLoading, getDashboardPath } = useAuth();

  if (isLoading) {
    return <LoadingScreen />;
  }

  if (isAuthenticated) {
    return <Navigate to={getDashboardPath()} />;
  }

  return children;
};

/**
 * Main app routes wrapped with AuthProvider
 */
const AppRoutes = () => {
  return (
    <Routes>
      <Route
        path="/"
        element={
          <PublicRoute>
            <LandingPage />
          </PublicRoute>
        }
      />
      <Route
        path="/login"
        element={
          <PublicRoute>
            <Login />
          </PublicRoute>
        }
      />
      <Route
        path="/signup"
        element={
          <PublicRoute>
            <Signup />
          </PublicRoute>
        }
      />
      <Route
        path="/faculty/signup"
        element={
          <PublicRoute>
            <FacultySignup />
          </PublicRoute>
        }
      />
      <Route
        path="/dashboard"
        element={
          <StudentRoute>
            <StudentDashboard />
          </StudentRoute>
        }
      />
      <Route
        path="/faculty/dashboard"
        element={
          <FacultyRoute>
            <FacultyDashboard />
          </FacultyRoute>
        }
      />
      <Route
        path="/admin/dashboard"
        element={
          <AdminRoute>
            <AdminDashboard />
          </AdminRoute>
        }
      />
    </Routes>
  );
};

function App() {
  return (
    <Router>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </Router>
  );
}

export default App;
