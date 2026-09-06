import { useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import LmsLogo from "./common/LmsLogo";

const LandingPage = () => {
  const navigate = useNavigate();
  const [activeDay, setActiveDay] = useState(3);

  useEffect(() => {
    const observerOptions = {
      threshold: 0.1,
      rootMargin: "0px 0px -50px 0px",
    };

    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("animate-fade-in");
        }
      });
    }, observerOptions);

    const elements = document.querySelectorAll(".animate-on-scroll");
    elements.forEach((el) => observer.observe(el));

    return () => {
      elements.forEach((el) => observer.unobserve(el));
    };
  }, []);

  const weeklyData = [40, 65, 50, 85, 45, 60, 30];
  const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

  return (
    <div className="min-h-screen bg-[#EAEBEB]">
      {/* Fixed Header */}
      <header className="fixed top-4 left-4 right-4 z-50 top-2 left-4 right-4 z-50 mx-auto max-w-7xl">
        <div className="flex justify-between items-center px-8 py-4 bg-white/10 backdrop-blur-2xl rounded-full border border-white/20 shadow-xl shadow-black/5 animate-on-scroll">
          <div className="flex items-center gap-3">
            <LmsLogo size={36} />
            <span className="font-bold tracking-tight text-xl text-slate-900">
              LMS Enterprise
            </span>
          </div>
          <nav className="hidden md:flex gap-8 text-sm font-medium text-[#666666]">
            <a href="#" className="hover:text-black transition-colors">
              Solutions
            </a>
            <a href="#" className="hover:text-black transition-colors">
              Pricing
            </a>
            <a href="#" className="hover:text-black transition-colors">
              Resources
            </a>
          </nav>
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate("/login")}
              className="text-sm font-semibold hover:opacity-70 transition-opacity"
            >
              Login
            </button>
            <button
              onClick={() => navigate("/signup")}
              className="px-6 py-2.5 bg-black text-white text-sm font-semibold rounded-full hover:scale-105 transition-transform"
            >
              Get Started
            </button>
          </div>
        </div>
      </header>{" "}
      {/* Main Content with top padding to account for fixed header */}
      <div className="pt-[36rem] p-4 md:p-8">
        <div className="mt-24 max-w-7xl mx-auto space-y-6">
          <main className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Hero Section */}
            <section className="lg:col-span-7 bg-[#F4F5F5] rounded-[2.5rem] p-12 md:p-16 flex flex-col justify-center min-h-[500px] border border-white/40 shadow-[0_10px_30px_-5px_rgba(0,0,0,0.04)] hover:shadow-[0_20px_40px_-5px_rgba(0,0,0,0.08)] transition-all duration-500 animate-on-scroll">
              <h1 className="font-serif text-6xl md:text-8xl leading-[0.9] mb-8 text-[#2D2D2D]">
                Master your future with AI-guided learning
              </h1>
              <p className="text-xl text-[#666666] max-w-md mb-10 leading-relaxed">
                Personalized paths, intelligent assistance, and boundless
                knowledge await.
              </p>
              <div className="flex flex-wrap gap-4">
                <button
                  onClick={() => navigate("/signup")}
                  className="px-8 py-4 bg-[#BDE3FF] text-black font-bold rounded-full hover:brightness-95 transition-all shadow-sm hover:shadow-md"
                >
                  Start Your Journey
                </button>
                <button className="px-8 py-4 bg-white/60 border border-white font-bold rounded-full hover:bg-white transition-all flex items-center gap-2">
                  <svg
                    className="w-6 h-6"
                    fill="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path d="M8 5v14l11-7z" />
                  </svg>
                  Watch Demo
                </button>
              </div>
            </section>

            {/* Weekly Progress Card */}
            <section className="lg:col-span-5 bg-[#F4F5F5] rounded-[2.5rem] p-8 flex flex-col justify-between border border-white/40 shadow-[0_10px_30px_-5px_rgba(0,0,0,0.04)] hover:shadow-[0_20px_40px_-5px_rgba(0,0,0,0.08)] transition-all duration-500 animate-on-scroll">
              <div>
                <div className="flex justify-between items-start mb-8">
                  <div>
                    <span className="text-xs font-bold uppercase tracking-widest text-[#666666]">
                      Activity
                    </span>
                    <h3 className="text-2xl font-bold text-[#2D2D2D]">
                      Weekly Progress
                    </h3>
                  </div>
                  <div className="w-12 h-12 bg-[#C1F1C6] rounded-full flex items-center justify-center shadow-sm">
                    <span className="font-bold text-lg">70%</span>
                  </div>
                </div>
                <div className="flex items-end justify-between h-48 gap-3 px-2">
                  {weeklyData.map((height, i) => (
                    <div
                      key={i}
                      className={`flex-1 rounded-t-2xl transition-all duration-300 cursor-pointer ${
                        i === activeDay ? "bg-[#BDE3FF]/60" : "bg-[#BDE3FF]/30"
                      } hover:bg-[#BDE3FF]/60`}
                      style={{ height: `${height}%` }}
                      onMouseEnter={() => setActiveDay(i)}
                    ></div>
                  ))}
                </div>
                <div className="flex justify-between text-[10px] font-bold text-[#666666] mt-4 uppercase tracking-tighter">
                  {days.map((day, i) => (
                    <span key={i}>{day}</span>
                  ))}
                </div>
              </div>
              <div className="mt-8 p-4 bg-white/40 rounded-3xl border border-white/60 shadow-inner">
                <p className="text-sm font-medium">
                  You're performing better than{" "}
                  <span className="text-black font-bold">85%</span> of peers
                  this week!
                </p>
              </div>
            </section>

            {/* Video Lectures & Smart Notes */}
            <section className="lg:col-span-4 bg-[#F4F5F5] rounded-[2.5rem] p-8 overflow-hidden border border-white/40 shadow-[0_10px_30px_-5px_rgba(0,0,0,0.04)] hover:shadow-[0_20px_40px_-5px_rgba(0,0,0,0.08)] transition-all duration-500 animate-on-scroll">
              <h3 className="text-2xl font-bold mb-6 text-[#2D2D2D]">
                Video Lectures &<br />
                Smart Notes
              </h3>
              <div className="relative group mb-6">
                <div className="aspect-video bg-[#E8D9FF] rounded-3xl overflow-hidden border-4 border-white shadow-lg">
                  <div className="w-full h-full bg-gradient-to-br from-[#E8D9FF] to-[#BDE3FF] flex items-center justify-center">
                    <div className="w-16 h-16 bg-white rounded-full flex items-center justify-center shadow-xl group-hover:scale-110 transition-transform cursor-pointer">
                      <svg
                        className="w-8 h-8 ml-1"
                        fill="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path d="M8 5v14l11-7z" />
                      </svg>
                    </div>
                  </div>
                </div>
              </div>
              <div className="space-y-3">
                <div className="flex items-center gap-3 p-3 bg-white/50 rounded-2xl border border-white/40 hover:bg-white/70 transition-colors cursor-pointer">
                  <div className="w-8 h-8 bg-[#C1F1C6] rounded-lg flex items-center justify-center">
                    <svg
                      className="w-4 h-4"
                      fill="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z" />
                    </svg>
                  </div>
                  <div className="flex-1">
                    <div className="h-2 w-24 bg-black/10 rounded-full mb-1"></div>
                    <div className="h-1.5 w-16 bg-black/5 rounded-full"></div>
                  </div>
                </div>
                <div className="flex items-center gap-3 p-3 bg-white/50 rounded-2xl border border-white/40 hover:bg-white/70 transition-colors cursor-pointer">
                  <div className="w-8 h-8 bg-[#BDE3FF] rounded-lg flex items-center justify-center">
                    <svg
                      className="w-4 h-4"
                      fill="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path d="M9 2a1 1 0 0 0-1 1v2H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2V3a1 1 0 1 0-2 0v2H9V3a1 1 0 0 0-1-1z" />
                    </svg>
                  </div>
                  <div className="flex-1">
                    <div className="h-2 w-32 bg-black/10 rounded-full mb-1"></div>
                    <div className="h-1.5 w-20 bg-black/5 rounded-full"></div>
                  </div>
                </div>
              </div>
            </section>

            {/* AI-Powered Learning Path */}
            <section className="lg:col-span-8 bg-[#BDE3FF]/10 rounded-[2.5rem] p-10 border border-[#BDE3FF]/20 shadow-[0_10px_30px_-5px_rgba(0,0,0,0.04)] hover:shadow-[0_20px_40px_-5px_rgba(0,0,0,0.08)] transition-all duration-500 animate-on-scroll">
              <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 mb-12">
                <div>
                  <h3 className="text-3xl font-bold mb-2 text-[#2D2D2D]">
                    AI-Powered Learning Path
                  </h3>
                  <p className="text-[#666666]">
                    Your personalized journey, guided by AI
                  </p>
                </div>
                <button className="px-6 py-3 bg-white border border-white rounded-full font-bold shadow-sm hover:shadow-md transition-all">
                  Resume Learning
                </button>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 relative">
                <div className="hidden md:block absolute top-12 left-[20%] right-[20%] h-0.5 bg-black/5"></div>

                {/* Completed */}
                <div className="relative z-10 text-center space-y-4">
                  <div className="w-24 h-24 mx-auto bg-[#C1F1C6] rounded-full flex items-center justify-center border-4 border-white shadow-inner">
                    <svg
                      className="w-8 h-8"
                      fill="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z" />
                    </svg>
                  </div>
                  <div>
                    <h4 className="font-bold text-[#2D2D2D]">Introduction</h4>
                    <span className="px-3 py-1 bg-white/60 rounded-full text-[10px] font-bold uppercase">
                      Completed
                    </span>
                  </div>
                </div>

                {/* Current */}
                <div className="relative z-10 text-center space-y-4">
                  <div className="w-24 h-24 mx-auto bg-white rounded-full flex items-center justify-center border-4 border-[#BDE3FF] shadow-lg animate-pulse">
                    <svg
                      className="w-8 h-8 text-[#BDE3FF]"
                      fill="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path d="M13 2L3 14h8l-1 8 10-12h-8l1-8z" />
                    </svg>
                  </div>
                  <div>
                    <h4 className="font-bold text-[#2D2D2D]">Core Concepts</h4>
                    <span className="px-3 py-1 bg-[#BDE3FF] text-black rounded-full text-[10px] font-bold uppercase">
                      Current
                    </span>
                  </div>
                </div>

                {/* Locked */}
                <div className="relative z-10 text-center space-y-4">
                  <div className="w-24 h-24 mx-auto bg-white/40 rounded-full flex items-center justify-center border-4 border-white/20">
                    <svg
                      className="w-8 h-8 text-black/20"
                      fill="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zm-6 9c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm3.1-9H8.9V6c0-1.71 1.39-3.1 3.1-3.1 1.71 0 3.1 1.39 3.1 3.1v2z" />
                    </svg>
                  </div>
                  <div>
                    <h4 className="font-bold opacity-40 text-[#2D2D2D]">
                      Advanced Methods
                    </h4>
                    <span className="px-3 py-1 bg-black/5 rounded-full text-[10px] font-bold uppercase opacity-40">
                      Locked
                    </span>
                  </div>
                </div>
              </div>
            </section>

            {/* Global Community */}
            <section className="lg:col-span-12 bg-[#F4F5F5] rounded-[2.5rem] p-8 md:p-12 overflow-hidden relative min-h-[400px] flex items-center border border-white/40 shadow-[0_10px_30px_-5px_rgba(0,0,0,0.04)] hover:shadow-[0_20px_40px_-5px_rgba(0,0,0,0.08)] transition-all duration-500 animate-on-scroll">
              <div className="grid md:grid-cols-2 gap-12 w-full items-center">
                <div className="max-w-lg z-10">
                  <h3 className="text-4xl md:text-5xl font-bold mb-6 text-[#2D2D2D]">
                    Join a Global Community of Learners
                  </h3>
                  <p className="text-lg text-[#666666] mb-8">
                    Connect with peers, share knowledge, and grow together in
                    our vibrant study groups.
                  </p>
                  <div className="flex items-center gap-6">
                    <button
                      onClick={() => navigate("/signup")}
                      className="px-8 py-4 bg-black text-white rounded-full font-bold hover:bg-black/80 transition-all"
                    >
                      Join Now
                    </button>
                    <div className="flex -space-x-3">
                      <div className="w-12 h-12 rounded-full border-4 border-[#F4F5F5] bg-gradient-to-br from-blue-400 to-blue-600"></div>
                      <div className="w-12 h-12 rounded-full border-4 border-[#F4F5F5] bg-gradient-to-br from-purple-400 to-purple-600"></div>
                      <div className="w-12 h-12 rounded-full border-4 border-[#F4F5F5] bg-gradient-to-br from-green-400 to-green-600"></div>
                      <div className="w-12 h-12 rounded-full border-4 border-[#F4F5F5] bg-[#E8D9FF] flex items-center justify-center text-xs font-bold">
                        +2k
                      </div>
                    </div>
                  </div>
                </div>
                <div className="relative">
                  <div className="aspect-[4/3] rounded-[2.5rem] overflow-hidden border-8 border-white shadow-2xl rotate-2 hover:rotate-0 transition-transform duration-500 bg-gradient-to-br from-[#BDE3FF] to-[#E8D9FF] flex items-center justify-center">
                    <svg
                      className="w-32 h-32 text-white/40"
                      fill="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z" />
                    </svg>
                  </div>
                </div>
              </div>
            </section>
          </main>

          {/* Footer */}
          <footer className="bg-[#C1F1C6] rounded-[2.5rem] p-12 md:p-16 animate-on-scroll">
            <div className="grid grid-cols-1 md:grid-cols-12 gap-12">
              <div className="md:col-span-5">
                <div className="flex items-center gap-2 mb-6">
                  <LmsLogo size={40} />
                  <span className="font-bold text-2xl tracking-tighter">
                    LMS — Future of Learning
                  </span>
                </div>
                <p className="text-black/60 mb-8 max-w-xs">
                  © 2024 LMS Enterprise Inc. All rights reserved. Designed for
                  the curious mind.
                </p>
                <div className="flex gap-4">
                  <a
                    href="#"
                    className="w-10 h-10 bg-white/40 rounded-full flex items-center justify-center hover:bg-white transition-all"
                  >
                    <svg
                      className="w-5 h-5"
                      fill="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path d="M24 4.557c-.883.392-1.832.656-2.828.775 1.017-.609 1.798-1.574 2.165-2.724-.951.564-2.005.974-3.127 1.195-.897-.957-2.178-1.555-3.594-1.555-3.179 0-5.515 2.966-4.797 6.045-4.091-.205-7.719-2.165-10.148-5.144-1.29 2.213-.669 5.108 1.523 6.574-.806-.026-1.566-.247-2.229-.616-.054 2.281 1.581 4.415 3.949 4.89-.693.188-1.452.232-2.224.084.626 1.956 2.444 3.379 4.6 3.419-2.07 1.623-4.678 2.348-7.29 2.04 2.179 1.397 4.768 2.212 7.548 2.212 9.142 0 14.307-7.721 13.995-14.646.962-.695 1.797-1.562 2.457-2.549z" />
                    </svg>
                  </a>
                  <a
                    href="#"
                    className="w-10 h-10 bg-white/40 rounded-full flex items-center justify-center hover:bg-white transition-all"
                  >
                    <svg
                      className="w-5 h-5"
                      fill="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z" />
                    </svg>
                  </a>
                  <a
                    href="#"
                    className="w-10 h-10 bg-white/40 rounded-full flex items-center justify-center hover:bg-white transition-all"
                  >
                    <svg
                      className="w-5 h-5"
                      fill="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path d="M19.615 3.184c-3.604-.246-11.631-.245-15.23 0-3.897.266-4.356 2.62-4.385 8.816.029 6.185.484 8.549 4.385 8.816 3.6.245 11.626.246 15.23 0 3.897-.266 4.356-2.62 4.385-8.816-.029-6.185-.484-8.549-4.385-8.816zm-10.615 12.816v-8l8 4-8 4z" />
                    </svg>
                  </a>
                </div>
              </div>
              <div className="md:col-span-2">
                <h4 className="font-bold mb-6">Company</h4>
                <ul className="space-y-4 text-black/60 font-medium">
                  <li>
                    <a href="#" className="hover:text-black">
                      About
                    </a>
                  </li>
                  <li>
                    <a href="#" className="hover:text-black">
                      Careers
                    </a>
                  </li>
                  <li>
                    <a href="#" className="hover:text-black">
                      Blog
                    </a>
                  </li>
                </ul>
              </div>
              <div className="md:col-span-2">
                <h4 className="font-bold mb-6">Support</h4>
                <ul className="space-y-4 text-black/60 font-medium">
                  <li>
                    <a href="#" className="hover:text-black">
                      Help Center
                    </a>
                  </li>
                  <li>
                    <a href="#" className="hover:text-black">
                      Safety
                    </a>
                  </li>
                  <li>
                    <a href="#" className="hover:text-black">
                      Privacy
                    </a>
                  </li>
                </ul>
              </div>
              <div className="md:col-span-3">
                <h4 className="font-bold mb-6">Contact</h4>
                <div className="flex items-center gap-3 p-4 bg-white/30 rounded-2xl border border-white/40">
                  <div className="w-2 h-2 bg-black rounded-full animate-pulse"></div>
                  <span className="text-sm font-bold">Systems operational</span>
                </div>
              </div>
            </div>
          </footer>
        </div>
      </div>
    </div>
  );
};

export default LandingPage;
