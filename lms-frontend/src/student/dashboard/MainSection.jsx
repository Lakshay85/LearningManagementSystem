import { useAuth } from "../../hooks/useAuth";
import RecommendedVideos from "./RecommendedVideos";

const MainSection = ({ onToggleNotifications }) => {
  const { user } = useAuth();

  return (
    <div className="max-w-7xl mx-auto font-sans">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-10">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Overview</h1>
          <p className="text-slate-500 mt-1">
            Hello {user.firstName || "Alex"}, welcome back to your learning journey!
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="relative hidden lg:block">
            <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-xl">search</span>
            <input
              className="pl-10 pr-4 py-2.5 w-64 rounded-xl border-none bg-white shadow-sm text-sm focus:ring-2 focus:ring-[#6366f1]/20 outline-none"
              placeholder="Search Dashboard"
              type="text"
            />
          </div>
          <button
            onClick={onToggleNotifications}
            className="p-2.5 rounded-xl bg-white text-slate-500 shadow-sm hover:shadow-md transition-all relative border-none outline-none group"
          >
            <span className="material-symbols-outlined group-hover:text-indigo-600 transition-colors">notifications</span>
            <span className="absolute top-2.5 right-2.5 size-2 bg-red-500 rounded-full border-2 border-white"></span>
          </button>
        </div>
      </div>

      {/* Welcome Card */}
      <div className="w-full bg-indigo-600 rounded-[2.5rem] p-10 shadow-xl shadow-indigo-500/10 mb-8 relative overflow-hidden text-white">
        <div className="relative z-10 max-w-2xl">
          <h2 className="text-3xl font-bold mb-3">Welcome Back, {user.firstName || "Alex"}! 👋</h2>
          <p className="text-indigo-100 text-lg font-light leading-relaxed">
            Consistency is the key to mastery. You've completed 75% of your weekly targets—keep pushing forward to reach your full potential!
          </p>
          <button className="mt-8 px-6 py-3 bg-white text-indigo-600 font-bold rounded-2xl hover:bg-indigo-50 transition-colors shadow-lg">
            Continue Learning
          </button>
        </div>
        <div className="absolute -right-20 -top-20 size-64 bg-indigo-500/30 rounded-full blur-3xl"></div>
        <div className="absolute right-20 -bottom-10 size-48 bg-indigo-400/20 rounded-full blur-2xl"></div>
      </div>

      {/* Recommended Videos */}
      <RecommendedVideos />

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
        {/* Daily Learning Activity */}
        <div className="lg:col-span-2 bg-white rounded-[2.5rem] p-8 shadow-sm border border-slate-100">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="text-xl font-bold text-slate-900">Daily Learning Activity</h2>
              <p className="text-sm text-slate-500">Time you spent every day on learning</p>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-4 bg-slate-50 px-4 py-2 rounded-xl text-xs font-medium text-slate-500">
                <span className="material-symbols-outlined text-sm">calendar_today</span>
                21 Nov 21 - 28 Nov 21
              </div>
            </div>
          </div>
          <div className="h-64 relative mt-10">
            <div className="absolute inset-0 flex flex-col justify-between text-[10px] text-slate-400 font-medium">
              <span className="border-b border-slate-50 pb-2">12 Hrs</span>
              <span className="border-b border-slate-50 pb-2">9 Hrs</span>
              <span className="border-b border-slate-50 pb-2">6 Hrs</span>
              <span className="border-b border-slate-50 pb-2">3 Hrs</span>
              <span className="border-b border-slate-50 pb-2">0 Hrs</span>
            </div>
            <svg className="absolute inset-0 w-full h-full pt-2 pb-6" preserveAspectRatio="none" viewBox="0 0 1000 100">
              <path d="M0,60 Q150,20 300,50 T600,30 T900,40 L1000,45" fill="none" stroke="#8b5cf6" strokeLinecap="round" strokeWidth="3"></path>
              <path d="M0,80 Q200,60 400,75 T700,55 T1000,65" fill="none" stroke="#14b8a6" strokeLinecap="round" strokeWidth="3"></path>
            </svg>
            <div className="absolute bottom-0 w-full flex justify-between px-2 text-[10px] font-bold text-slate-400">
              <span>1 Jan</span><span>2 Jan</span><span>3 Jan</span><span>4 Jan</span><span>5 Jan</span><span>6 Jan</span><span>7 Jan</span><span>8 Jan</span>
            </div>
          </div>
        </div>

        {/* Weekly Status */}
        <div className="bg-white rounded-[2.5rem] p-8 shadow-sm border border-slate-100">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="text-xl font-bold text-slate-900">Weekly Status</h2>
              <p className="text-sm text-slate-500">From 12 Oct - 24 Nov</p>
            </div>
            <span className="material-symbols-outlined text-slate-400">bar_chart</span>
          </div>
          <div className="flex items-end justify-between h-56 gap-2 px-2">
            <div className="w-full bg-gradient-to-t from-cyan-400 to-cyan-300 rounded-full h-[60%]"></div>
            <div className="w-full bg-gradient-to-t from-indigo-600 to-[#8b5cf6] rounded-full h-[85%]"></div>
            <div className="w-full bg-gradient-to-t from-cyan-400 to-cyan-300 rounded-full h-[45%]"></div>
            <div className="w-full bg-gradient-to-t from-indigo-600 to-[#8b5cf6] rounded-full h-[75%]"></div>
            <div className="w-full bg-gradient-to-t from-cyan-400 to-cyan-300 rounded-full h-[55%]"></div>
            <div className="w-full bg-gradient-to-t from-indigo-600 to-[#8b5cf6] rounded-full h-[95%]"></div>
            <div className="w-full bg-gradient-to-t from-cyan-400 to-cyan-300 rounded-full h-[65%]"></div>
            <div className="w-full bg-gradient-to-t from-indigo-600 to-[#8b5cf6] rounded-full h-[70%]"></div>
            <div className="w-full bg-gradient-to-t from-cyan-400 to-cyan-300 rounded-full h-[80%]"></div>
          </div>
          <div className="grid grid-cols-2 gap-4 mt-8 pt-8 border-t border-slate-50">
            <div>
              <p className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Minimum</p>
              <p className="text-xl font-bold text-slate-900">4 Hrs</p>
            </div>
            <div className="text-right">
              <p className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Maximum</p>
              <p className="text-xl font-bold text-slate-900">8 Hrs</p>
            </div>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8 mb-8">
        {/* Daily Learning Objectives */}
        <div className="lg:col-span-3 bg-white rounded-[2.5rem] p-8 shadow-sm border border-slate-100">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="text-xl font-bold text-slate-900">Daily Learning Objectives</h2>
              <p className="text-sm text-slate-500">Keep up with your scheduled tasks for today</p>
            </div>
            <div className="px-4 py-2 bg-[#6366f1]/10 text-[#6366f1] rounded-xl text-xs font-bold">
              3/5 COMPLETED
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-6 bg-purple-50 rounded-3xl border border-purple-100/50 group hover:border-purple-300 transition-all cursor-pointer">
              <div className="flex justify-between items-start mb-6">
                <div className="size-12 rounded-2xl bg-white flex items-center justify-center text-purple-600 shadow-sm">
                  <span className="material-symbols-outlined">play_circle</span>
                </div>
                <div className="size-6 rounded-full bg-purple-600 flex items-center justify-center text-white">
                  <span className="material-symbols-outlined text-xs">check</span>
                </div>
              </div>
              <h4 className="font-bold text-purple-950 mb-1">Watch 2 Videos</h4>
              <p className="text-xs text-purple-600/70 font-medium">LMS Architecture Course</p>
            </div>
            <div className="p-6 bg-teal-50 rounded-3xl border border-teal-100/50 group hover:border-teal-300 transition-all cursor-pointer">
              <div className="flex justify-between items-start mb-6">
                <div className="size-12 rounded-2xl bg-white flex items-center justify-center text-teal-600 shadow-sm">
                  <span className="material-symbols-outlined">quiz</span>
                </div>
                <div className="size-6 rounded-full border-2 border-teal-200"></div>
              </div>
              <h4 className="font-bold text-teal-950 mb-1">Complete Quiz</h4>
              <p className="text-xs text-teal-600/70 font-medium">Data Structures Basics</p>
            </div>
            <div className="p-6 bg-pink-50 rounded-3xl border border-pink-100/50 group hover:border-pink-300 transition-all cursor-pointer">
              <div className="flex justify-between items-start mb-6">
                <div className="size-12 rounded-2xl bg-white flex items-center justify-center text-pink-600 shadow-sm">
                  <span className="material-symbols-outlined">timer</span>
                </div>
                <div className="size-6 rounded-full border-2 border-pink-200"></div>
              </div>
              <h4 className="font-bold text-pink-950 mb-1">1 Hour Study</h4>
              <p className="text-xs text-pink-600/70 font-medium">Algorithm Design</p>
            </div>
          </div>
        </div>

        {/* Progress Circle */}
        <div className="bg-amber-50 rounded-[2.5rem] p-8 shadow-sm border border-amber-100/50">
          <div className="flex items-center justify-between mb-6">
            <h3 className="font-bold text-amber-900">Progress</h3>
            <div className="bg-white p-2 rounded-xl text-amber-600 shadow-sm">
              <span className="material-symbols-outlined text-lg">trending_up</span>
            </div>
          </div>
          <div className="flex flex-col items-center">
            <div className="relative size-32 mb-4">
              <svg className="size-full -rotate-90" viewBox="0 0 100 100">
                <circle className="text-amber-100" cx="50" cy="50" fill="transparent" r="40" stroke="currentColor" strokeWidth="8"></circle>
                <circle className="text-amber-500" cx="50" cy="50" fill="transparent" r="40" stroke="currentColor" strokeDasharray="251.2" strokeDashoffset="62.8" strokeLinecap="round" strokeWidth="8"></circle>
              </svg>
              <div className="absolute inset-0 flex items-center justify-center font-bold text-xl text-amber-900">75%</div>
            </div>
            <p className="text-xs font-medium text-amber-600">Week Streak: 12 Days</p>
          </div>
        </div>
      </div>

      {/* Bottom Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {/* Quick Tasks */}
        <div className="bg-indigo-50 rounded-[2.5rem] p-8 shadow-sm border border-indigo-100/50">
          <div className="flex items-center justify-between mb-6">
            <h3 className="font-bold text-indigo-900">Quick Tasks</h3>
            <div className="bg-white p-2 rounded-xl text-indigo-600 shadow-sm">
              <span className="material-symbols-outlined text-lg">fact_check</span>
            </div>
          </div>
          <div className="space-y-3">
            <div className="flex items-center gap-3 p-4 bg-white/80 rounded-2xl shadow-sm border border-white/50">
              <div className="size-6 rounded-lg bg-indigo-600 flex items-center justify-center text-white">
                <span className="material-symbols-outlined text-sm">check</span>
              </div>
              <span className="text-sm font-medium text-indigo-950">Submit Design Essay</span>
            </div>
            <div className="flex items-center gap-3 p-4 bg-white/80 rounded-2xl shadow-sm border border-white/50">
              <div className="size-6 rounded-lg border-2 border-indigo-200"></div>
              <span className="text-sm font-medium text-indigo-950">Watch Lecture 4</span>
            </div>
          </div>
        </div>

        {/* Smart Notes Summary */}
        <div className="bg-emerald-50 rounded-[2.5rem] p-8 shadow-sm border border-emerald-100/50 md:col-span-2">
          <div className="flex items-center justify-between mb-6">
            <h3 className="font-bold text-emerald-900">Smart Notes Summary</h3>
            <div className="bg-white p-2 rounded-xl text-emerald-600 shadow-sm">
              <span className="material-symbols-outlined text-lg">add</span>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 bg-white/80 rounded-2xl shadow-sm border border-white/50">
              <p className="text-xs font-bold text-emerald-500 uppercase mb-1">UI Principles</p>
              <p className="text-sm text-emerald-900">Review Gestalt principles for Friday's quiz on visual hierarchy.</p>
            </div>
            <div className="p-4 bg-white/80 rounded-2xl shadow-sm border border-white/50">
              <p className="text-xs font-bold text-emerald-500 uppercase mb-1">Color Theory</p>
              <p className="text-sm text-emerald-900">Check accessibility standards for contrast ratios in dark mode.</p>
            </div>
          </div>
        </div>
      </div>

      <div className="h-10"></div>
    </div>
  );
};

export default MainSection;
