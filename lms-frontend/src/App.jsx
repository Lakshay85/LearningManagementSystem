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

/**
 * Loading component shown during auth check
 */
const LoadingScreen = () => (
  <div className="min-h-screen flex items-center justify-center bg-gray-50">
    <div className="flex flex-col items-center gap-4">
      <div className="w-12 h-12 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
      <p className="text-gray-600 font-medium">Loading...</p>
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
  if (role !== "teacher" && role !== "faculty") {
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
