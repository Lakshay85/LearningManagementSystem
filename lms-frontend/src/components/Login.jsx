import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { authAPI } from "../utils/api";

const Login = () => {
  const navigate = useNavigate();
  const { refreshUser } = useAuth();
  const [formData, setFormData] = useState({
    email: "",
    password: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
    if (error) setError("");
  };

  const getDashboardPath = (role) => {
    switch (role) {
      case "teacher":
      case "faculty":
        return "/faculty/dashboard";
      case "admin":
        return "/admin/dashboard";
      case "student":
      default:
        return "/dashboard";
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const response = await authAPI.login({
        email: formData.email,
        password: formData.password,
      });

      // Refresh user state from the auth context
      await refreshUser();

      const dashboardPath = getDashboardPath(response.user.role);
      navigate(dashboardPath);
    } catch (err) {
      console.error("Login error:", err);
      setError(err.message || "Login failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-soft-bg flex flex-col p-4 md:p-8 font-sans text-text-main">
      <div className="max-w-7xl mx-auto w-full flex flex-col flex-1">
        {/* Header */}
        <header className="flex justify-between items-center px-8 py-4 mb-8">
          <div className="flex items-center gap-2">
            <div className="size-8 bg-black rounded-lg flex items-center justify-center text-white">
              <span className="material-symbols-outlined text-sm">circle</span>
            </div>
            <span className="font-bold tracking-tight text-xl">LMS</span>
          </div>
          <nav className="flex gap-6 text-sm font-medium text-text-sub">
            <a href="#" className="hover:text-black transition-colors">
              Help
            </a>
            <a href="#" className="hover:text-black transition-colors">
              Privacy
            </a>
          </nav>
        </header>

        {/* Main Content */}
        <main className="flex-1 flex items-center justify-center py-6">
          <div className="bg-white rounded-card shadow-card overflow-hidden border border-white/40 w-full max-w-5xl grid grid-cols-1 lg:grid-cols-2 min-h-[600px]">
            {/* Left Panel - Lavender */}
            <div className="bg-lavender p-12 flex flex-col justify-between relative overflow-hidden">
              <div className="relative z-10">
                <h1 className="font-serif text-6xl md:text-7xl leading-[0.9] mb-6">
                  Welcome Back
                </h1>
                <p className="text-xl text-text-main/70 max-w-xs leading-relaxed">
                  Log in to continue your AI-guided learning journey and master
                  your future.
                </p>
              </div>

              <div className="relative z-10 flex flex-col gap-4">
                <div className="flex items-center gap-3 p-4 bg-white/40 backdrop-blur-sm rounded-3xl border border-white/40 w-fit">
                  <div className="size-10 bg-mint rounded-full flex items-center justify-center">
                    <span className="material-symbols-outlined">
                      auto_awesome
                    </span>
                  </div>
                  <span className="text-sm font-bold">
                    85% Progress this week
                  </span>
                </div>
                <div className="flex items-center gap-3 p-4 bg-white/40 backdrop-blur-sm rounded-3xl border border-white/40 w-fit ml-8">
                  <div className="size-10 bg-sky rounded-full flex items-center justify-center">
                    <span className="material-symbols-outlined">menu_book</span>
                  </div>
                  <span className="text-sm font-bold">
                    New Course: AI Ethics
                  </span>
                </div>
              </div>

              {/* Background Blurs */}
              <div className="absolute -bottom-20 -left-20 size-64 bg-mint/30 rounded-full blur-3xl"></div>
              <div className="absolute -top-20 -right-20 size-64 bg-sky/30 rounded-full blur-3xl"></div>
            </div>

            {/* Right Panel - Form */}
            <div className="p-12 md:p-16 flex flex-col justify-center bg-white">
              <div className="max-w-sm mx-auto w-full">
                <div className="mb-10">
                  <h2 className="text-3xl font-bold mb-2">Sign In</h2>
                  <p className="text-text-sub">Choose your preferred method</p>
                </div>

                {error && (
                  <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm mb-6">
                    {error}
                  </div>
                )}

                <div className="space-y-3 mb-8">
                  <button
                    type="button"
                    className="w-full flex items-center justify-center gap-3 px-6 py-3.5 border border-gray-100 rounded-pill hover:bg-gray-50 transition-colors font-medium cursor-pointer"
                  >
                    <img
                      alt="Google"
                      className="w-5 h-5"
                      src="https://lh3.googleusercontent.com/aida-public/AB6AXuDKtiegvTA7QSjhNZ7CPk6ZGa99d1Zx3LwN-Rg6sygWmho7r1Ao3akd_5EyguIunZI7n1l7E9ex_Zj0MuhICr0IQbkRWEwwpwq5uHibl_ja2wvyrUiTy78OwTZJLURfd6K4dUdUQtigd4kWjDPNPHrnypzOPXeyNuuK1Ooam68__RbevexJOqCV6LhYshVa1EjSOqpcNNcYdwKp_4r3jduGTwoe7qTk3r03VCjdSR1oPw08YCu-9KOX40N62MEj3wpJXKy1A3RpGAfH"
                    />
                    Continue with Google
                  </button>
                  <button
                    type="button"
                    className="w-full flex items-center justify-center gap-3 px-6 py-3.5 border border-gray-100 rounded-pill hover:bg-gray-50 transition-colors font-medium cursor-pointer"
                  >
                    <img
                      alt="Microsoft"
                      className="w-5 h-5"
                      src="https://lh3.googleusercontent.com/aida-public/AB6AXuDDCH6ysnaMxZZ3IJX_j3W-2Xj--tkx8j5lxtnLU1-J8A3j6mNZQo72jINHkeMf_gb6R2TWWWdINhJqxjii3m10R-5GJq5pV1wKQsFa4_li-FdjEJ4vFttfopq2izvwx5bTJBolSEEP093dSKtSPsIuuO7MnlgQNO-4kcXqLurQRp7i77UsQnnUT3Wh12WgBax3GnNR27BhUnk-6_LTL5Pdi0RA9AufP4yACwnr4CMElSEEFEFd-iD_5xa9kISkYZMr3qtbkA8QKIZl"
                    />
                    Continue with Microsoft
                  </button>
                </div>

                <div className="relative mb-8">
                  <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t border-gray-100"></div>
                  </div>
                  <div className="relative flex justify-center text-xs uppercase tracking-widest text-text-sub">
                    <span className="bg-white px-4">Or use email</span>
                  </div>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">
                  <div>
                    <label className="block text-sm font-bold mb-2 px-1">
                      Email Address
                    </label>
                    <input
                      className="w-full px-6 py-4 bg-gray-50 border-transparent rounded-2xl focus:ring-2 focus:ring-sky/50 focus:bg-white focus:border-sky transition-all outline-none"
                      placeholder="name@company.com"
                      type="email"
                      name="email"
                      value={formData.email}
                      onChange={handleChange}
                      required
                    />
                  </div>
                  <div>
                    <div className="flex justify-between items-center mb-2 px-1">
                      <label className="text-sm font-bold">Password</label>
                      <a
                        className="text-xs font-bold text-sky-600 hover:text-sky-700"
                        href="#"
                      >
                        Forgot?
                      </a>
                    </div>
                    <input
                      className="w-full px-6 py-4 bg-gray-50 border-transparent rounded-2xl focus:ring-2 focus:ring-sky/50 focus:bg-white focus:border-sky transition-all outline-none"
                      placeholder="••••••••"
                      type="password"
                      name="password"
                      value={formData.password}
                      onChange={handleChange}
                      required
                    />
                  </div>
                  <button
                    className="w-full py-4 bg-sky text-black font-bold rounded-pill shadow-lg shadow-sky/20 hover:brightness-95 transition-all mt-6 cursor-pointer disabled:opacity-70 disabled:cursor-not-allowed"
                    type="submit"
                    disabled={loading}
                  >
                    {loading ? "Signing in..." : "Sign In to LMS"}
                  </button>
                </form>

                <p className="text-center text-sm text-text-sub mt-8">
                  Don't have an account?
                  <a
                    className="text-black font-bold hover:underline ml-1"
                    href="/signup"
                  >
                    Sign Up
                  </a>
                </p>
                <p className="text-center text-sm text-text-sub mt-3">
                  Want to join as a faculty?
                  <a
                    className="text-emerald-600 font-bold hover:underline ml-1"
                    href="/faculty/signup"
                  >
                    Faculty Sign Up
                  </a>
                </p>
              </div>
            </div>
          </div>
        </main>

        <footer className="mt-8 py-6 text-center">
          <p className="text-text-sub text-xs font-medium uppercase tracking-widest">
            © 2024 LMS Enterprise Inc. Secure Enterprise Access
          </p>
        </footer>
      </div>
    </div>
  );
};

export default Login;
