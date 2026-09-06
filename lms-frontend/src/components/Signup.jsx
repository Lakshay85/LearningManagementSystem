import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { authAPI } from "../utils/api";
import LmsLogo from "./common/LmsLogo";

const Signup = () => {
  const navigate = useNavigate();
  const { refreshUser } = useAuth();
  const [formData, setFormData] = useState({
    firstName: "",
    lastName: "",
    email: "",
    password: "",
    confirmPassword: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
    if (error) setError("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (formData.password !== formData.confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    if (formData.password.length < 8) {
      setError("Password must be at least 8 characters long.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      await authAPI.signup({
        firstName: formData.firstName,
        lastName: formData.lastName,
        email: formData.email,
        password: formData.password,
      });

      // Refresh user state from the auth context
      await refreshUser();
      navigate("/dashboard");
    } catch (err) {
      console.error("Signup error:", err);
      setError(err.message || "Signup failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#EAEBEB] px-4 md:px-8 py-6 flex items-center justify-center">
      <div className="max-w-6xl w-full mx-auto">
        {/* Logo */}
        <div className="flex justify-center mb-8">
          <Link to="/" className="flex items-center gap-3 group">
            <LmsLogo size={38} className="transition-transform group-hover:scale-105" />
            <span className="font-bold tracking-tight text-xl tracking-tight text-slate-900 group-hover:text-black transition-colors">
              LMS Enterprise
            </span>
          </Link>
        </div>

        <main className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
          {/* Left marketing panel */}
          <section className="lg:col-span-5 bg-[#C1F1C6] rounded-[2.5rem] p-10 md:p-12 flex flex-col justify-between overflow-hidden relative min-h-[480px] shadow-[0_10px_30px_-5px_rgba(0,0,0,0.04)]">
            <div className="relative z-10 space-y-8">
              <h1 className="font-serif text-4xl md:text-5xl leading-[1.1] text-black">
                Start your growth journey today.
              </h1>

              <div className="space-y-6 text-sm">
                <div className="flex gap-4 items-start">
                  <div className="w-12 h-12 bg-white/50 rounded-2xl flex items-center justify-center shrink-0">
                    <span className="text-lg">✨</span>
                  </div>
                  <div>
                    <h3 className="font-bold text-base">AI-Guided Paths</h3>
                    <p className="text-black/70 leading-relaxed">
                      Dynamic learning curriculums that adapt to your pace and
                      goals automatically.
                    </p>
                  </div>
                </div>

                <div className="flex gap-4 items-start">
                  <div className="w-12 h-12 bg-white/50 rounded-2xl flex items-center justify-center shrink-0">
                    <span className="text-lg">🌍</span>
                  </div>
                  <div>
                    <h3 className="font-bold text-base">Global Community</h3>
                    <p className="text-black/70 leading-relaxed">
                      Connect with professionals and students from around the
                      world.
                    </p>
                  </div>
                </div>

                <div className="flex gap-4 items-start">
                  <div className="w-12 h-12 bg-white/50 rounded-2xl flex items-center justify-center shrink-0">
                    <span className="text-lg">✅</span>
                  </div>
                  <div>
                    <h3 className="font-bold text-base">Enterprise Grade</h3>
                    <p className="text-black/70 leading-relaxed">
                      Secure, scalable, and trusted by leading institutions.
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-10 relative z-10">
              <div className="flex -space-x-3 mb-3">
                <div className="w-10 h-10 rounded-full border-2 border-[#C1F1C6] bg-gradient-to-br from-blue-400 to-blue-600" />
                <div className="w-10 h-10 rounded-full border-2 border-[#C1F1C6] bg-gradient-to-br from-purple-400 to-purple-600" />
                <div className="w-10 h-10 rounded-full border-2 border-[#C1F1C6] bg-gradient-to-br from-emerald-400 to-emerald-600" />
              </div>
              <p className="text-[11px] font-bold uppercase tracking-wider text-black/45">
                Join 2,000+ new learners this month
              </p>
            </div>

            <div className="absolute -bottom-12 -right-12 w-64 h-64 bg-white/30 rounded-full blur-3xl" />
          </section>

          {/* Right form panel */}
          <section className="lg:col-span-7 bg-[#F4F5F5] rounded-[2.5rem] p-10 md:p-16 flex flex-col justify-center shadow-[0_10px_30px_-5px_rgba(0,0,0,0.04)]">
            <div className="max-w-md mx-auto w-full">
              <div className="mb-8 text-center lg:text-left">
                <h2 className="text-3xl font-bold mb-2 text-[#2D2D2D]">
                  Create Account
                </h2>
                <p className="text-sm text-[#666666]">
                  Get started with your 14-day free trial.
                </p>
              </div>

              {error && (
                <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-2xl text-sm">
                  {error}
                </div>
              )}

              <form onSubmit={handleSubmit} className="space-y-5">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <label
                      htmlFor="firstName"
                      className="text-[11px] font-bold uppercase tracking-widest text-[#666666] ml-1"
                    >
                      First Name
                    </label>
                    <input
                      id="firstName"
                      name="firstName"
                      type="text"
                      required
                      value={formData.firstName}
                      onChange={handleChange}
                      placeholder="John"
                      className="w-full px-6 py-3.5 bg-white/70 border border-white rounded-2xl outline-none text-sm placeholder:text-[#666666]/60 focus:ring-2 focus:ring-[#BDE3FF] focus:border-[#BDE3FF] transition-all"
                    />
                  </div>

                  <div className="space-y-1">
                    <label
                      htmlFor="lastName"
                      className="text-[11px] font-bold uppercase tracking-widest text-[#666666] ml-1"
                    >
                      Last Name
                    </label>
                    <input
                      id="lastName"
                      name="lastName"
                      type="text"
                      required
                      value={formData.lastName}
                      onChange={handleChange}
                      placeholder="Doe"
                      className="w-full px-6 py-3.5 bg-white/70 border border-white rounded-2xl outline-none text-sm placeholder:text-[#666666]/60 focus:ring-2 focus:ring-[#BDE3FF] focus:border-[#BDE3FF] transition-all"
                    />
                  </div>
                </div>

                <div className="space-y-1">
                  <label
                    htmlFor="email"
                    className="text-[11px] font-bold uppercase tracking-widest text-[#666666] ml-1"
                  >
                    Work Email
                  </label>
                  <input
                    id="email"
                    name="email"
                    type="email"
                    required
                    value={formData.email}
                    onChange={handleChange}
                    placeholder="name@company.com"
                    className="w-full px-6 py-3.5 bg-white/70 border border-white rounded-2xl outline-none text-sm placeholder:text-[#666666]/60 focus:ring-2 focus:ring-[#BDE3FF] focus:border-[#BDE3FF] transition-all"
                  />
                </div>

                {/* Password */}
                <div className="space-y-1">
                  <label
                    htmlFor="password"
                    className="text-[11px] font-bold uppercase tracking-widest text-[#666666] ml-1"
                  >
                    Password
                  </label>
                  <div className="relative">
                    <input
                      id="password"
                      name="password"
                      type={showPassword ? "text" : "password"}
                      required
                      value={formData.password}
                      onChange={handleChange}
                      placeholder="••••••••"
                      className="w-full px-6 py-3.5 pr-12 bg-white/70 border border-white rounded-2xl outline-none text-sm placeholder:text-[#666666]/60 focus:ring-2 focus:ring-[#BDE3FF] focus:border-[#BDE3FF] transition-all"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword((prev) => !prev)}
                      className="absolute right-4 top-1/2 -translate-y-1/2 text-xs font-semibold text-[#666666] hover:text-black"
                    >
                      {showPassword ? "Hide" : "Show"}
                    </button>
                  </div>
                  <p className="text-[10px] text-[#666666] ml-1 italic">
                    Must be at least 8 characters with one special symbol.
                  </p>
                </div>

                {/* Confirm password */}
                <div className="space-y-1">
                  <label
                    htmlFor="confirmPassword"
                    className="text-[11px] font-bold uppercase tracking-widest text-[#666666] ml-1"
                  >
                    Confirm Password
                  </label>
                  <div className="relative">
                    <input
                      id="confirmPassword"
                      name="confirmPassword"
                      type={showConfirmPassword ? "text" : "password"}
                      required
                      value={formData.confirmPassword}
                      onChange={handleChange}
                      placeholder="Repeat your password"
                      className="w-full px-6 py-3.5 pr-12 bg-white/70 border border-white rounded-2xl outline-none text-sm placeholder:text-[#666666]/60 focus:ring-2 focus:ring-[#BDE3FF] focus:border-[#BDE3FF] transition-all"
                    />
                    <button
                      type="button"
                      onClick={() =>
                        setShowConfirmPassword((prev) => !prev)
                      }
                      className="absolute right-4 top-1/2 -translate-y-1/2 text-xs font-semibold text-[#666666] hover:text-black"
                    >
                      {showConfirmPassword ? "Hide" : "Show"}
                    </button>
                  </div>
                </div>

                <div className="pt-2">
                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full py-4 bg-[#BDE3FF] text-black font-bold rounded-2xl hover:brightness-95 hover:shadow-lg transition-all flex items-center justify-center gap-2 disabled:opacity-60 disabled:cursor-not-allowed"
                  >
                    {loading ? "Creating Account..." : "Create Account"}
                    {!loading && <span className="text-sm">→</span>}
                  </button>
                </div>

                <div className="relative py-4">
                  <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t border-black/5" />
                  </div>
                  <div className="relative flex justify-center">
                    <span className="bg-[#F4F5F5] px-4 text-[11px] font-bold text-[#666666] uppercase tracking-[0.2em]">
                      or sign up with
                    </span>
                  </div>
                </div>

                <div>
                  <button
                    type="button"
                    className="w-full flex items-center justify-center gap-3 py-3.5 bg-white border border-gray-200/80 rounded-2xl hover:bg-gray-50 hover:border-gray-300 shadow-sm transition-all duration-200 text-sm font-semibold text-slate-700 active:scale-[0.99] cursor-pointer"
                  >
                    <svg className="w-5 h-5 shrink-0" viewBox="0 0 24 24">
                      <path
                        fill="#4285F4"
                        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                      />
                      <path
                        fill="#34A853"
                        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                      />
                      <path
                        fill="#FBBC05"
                        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
                      />
                      <path
                        fill="#EA4335"
                        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
                      />
                    </svg>
                    Continue with Google
                  </button>
                </div>
              </form>

              <div className="mt-8 text-center">
                <p className="text-sm text-[#666666]">
                  Already have an account?
                  <Link
                    to="/login"
                    className="text-black font-bold hover:underline underline-offset-4 ml-1"
                  >
                    Log in
                  </Link>
                </p>
              </div>
            </div>
          </section>
        </main>

        <footer className="mt-6 text-center px-4">
          <p className="text-[11px] text-[#666666]">
            By signing up, you agree to our{" "}
            <a href="#" className="underline">
              Terms of Service
            </a>{" "}
            and{" "}
            <a href="#" className="underline">
              Privacy Policy
            </a>
            .
          </p>
        </footer>
      </div>
    </div>
  );
};

export default Signup;
