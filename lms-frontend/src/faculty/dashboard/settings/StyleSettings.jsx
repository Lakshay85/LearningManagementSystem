import { useState, useEffect } from "react";
import { Check, Palette, Eye, AlertCircle, RefreshCw } from "lucide-react";
import { applyThemeFonts } from "./themeUtils";

const StyleSettings = () => {
  const [currentTheme, setCurrentTheme] = useState(localStorage.getItem("faculty-theme") || "default");
  const [saveSuccess, setSaveSuccess] = useState(false);

  const stylePresets = [
    {
      id: "default",
      name: "Default Emerald",
      keywords: ["clean", "professional", "accessible"],
      headingFont: "Inter",
      bodyFont: "Inter",
      colors: ["#10b981", "#111827", "#f9fafb"],
      description: "The original clean white interface with emerald accents and crisp Inter typography.",
      previewStyles: {
        background: "#f9fafb",
        color: "#111827",
        border: "1px solid #e5e7eb",
        borderRadius: "0.75rem",
        boxShadow: "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
        fontFamily: "'Inter', sans-serif"
      },
      previewBadge: "bg-[#ecfdf5] text-[#10b981]"
    },
    {
      id: "glassmorphism",
      name: "Glassmorphism Blur",
      keywords: ["immersive", "frosted", "modern"],
      headingFont: "Outfit",
      bodyFont: "Inter",
      colors: ["#6366f1", "#ffffff", "#0f172a"],
      description: "Frosted semi-transparent glass cards, subtle white borders, backdrop blur, and colorful glowing backgrounds.",
      previewStyles: {
        background: "linear-gradient(135deg, #1e1b4b 0%, #0f172a 100%)",
        color: "#ffffff",
        border: "1px solid rgba(255, 255, 255, 0.1)",
        borderRadius: "1.25rem",
        boxShadow: "0 8px 32px 0 rgba(0, 0, 0, 0.3)",
        fontFamily: "'Inter', sans-serif",
        backdropFilter: "blur(8px)"
      },
      previewBadge: "bg-[rgba(99,102,241,0.2)] text-[#6366f1]"
    },
    {
      id: "claymorphism",
      name: "Playful Claymorphism",
      keywords: ["toy-like", "rounded", "bubbly"],
      headingFont: "Fredoka",
      bodyFont: "Nunito",
      colors: ["#a855f7", "#2e1065", "#f3e8ff"],
      description: "3D puffy card components, thick solid dark borders, inner and outer shadows, and a bubbly purple feel.",
      previewStyles: {
        background: "#f3e8ff",
        color: "#2e1065",
        border: "3px solid #2e1065",
        borderRadius: "1.5rem",
        boxShadow: "4px 4px 0px #2e1065, inset -2px -2px 6px rgba(147, 51, 234, 0.15)",
        fontFamily: "'Nunito', sans-serif"
      },
      previewBadge: "bg-[#e9d5ff] text-[#a855f7]"
    },
    {
      id: "minimalism",
      name: "Minimalist Swiss",
      keywords: ["stark", "monochromatic", "structural"],
      headingFont: "Space Grotesk",
      bodyFont: "Inter",
      colors: ["#000000", "#111827", "#ffffff"],
      description: "Stark simplicity, high contrast, geometric layouts, thin black borders, zero shadows, and strict type focus.",
      previewStyles: {
        background: "#ffffff",
        color: "#111827",
        border: "1px solid #111827",
        borderRadius: "0px",
        boxShadow: "none",
        fontFamily: "'Inter', sans-serif"
      },
      previewBadge: "bg-gray-100 text-black font-semibold"
    },
    {
      id: "bentogrid",
      name: "Bento Tech",
      keywords: ["dashboard-dense", "modular", "crisp"],
      headingFont: "Plus Jakarta Sans",
      bodyFont: "DM Sans",
      colors: ["#3b82f6", "#f9fafb", "#0b0f19"],
      description: "A dark theme showcasing dense bento card compartments, soft blue accents, and clean structured grid layouts.",
      previewStyles: {
        background: "#0b0f19",
        color: "#f9fafb",
        border: "1px solid #374151",
        borderRadius: "1rem",
        boxShadow: "0 4px 15px rgba(0, 0, 0, 0.3)",
        fontFamily: "'DM Sans', sans-serif"
      },
      previewBadge: "bg-[rgba(59,130,246,0.15)] text-[#3b82f6]"
    },
    {
      id: "neumorphism",
      name: "Neumorphism Soft",
      keywords: ["physical-depth", "dual-shadow", "clay"],
      headingFont: "Poppins",
      bodyFont: "Open Sans",
      colors: ["#6c63ff", "#3d4852", "#e0e5ec"],
      description: "Soft embossed and debossed physical visual depths using dual-shadow offset lighting on a solid clay grey base.",
      previewStyles: {
        background: "#e0e5ec",
        color: "#3d4852",
        border: "none",
        borderRadius: "1.5rem",
        boxShadow: "5px 5px 12px rgba(163,177,198,0.5), -5px -5px 12px rgba(255,255,255,0.8)",
        fontFamily: "'Open Sans', sans-serif"
      },
      previewBadge: "bg-[rgba(108,99,255,0.1)] text-[#6c63ff]"
    },
    {
      id: "brutalism",
      name: "Retro Brutalism",
      keywords: ["cyberpunk", "high-contrast", "raw"],
      headingFont: "Space Mono",
      bodyFont: "JetBrains Mono",
      colors: ["#ec4899", "#000000", "#fef08a"],
      description: "A loud yellow design, thick black outlines, offset hard black block shadows, and tech typewriter monospace fonts.",
      previewStyles: {
        background: "#ffffff",
        color: "#000000",
        border: "3px solid #000000",
        borderRadius: "0px",
        boxShadow: "4px 4px 0px #000000",
        fontFamily: "'JetBrains Mono', monospace"
      },
      previewBadge: "bg-[#fef08a] text-black border border-black font-mono text-xs px-1"
    },
    {
      id: "aurora",
      name: "Aurora Glow",
      keywords: ["cosmic", "glowing", "cyber-dark"],
      headingFont: "Syne",
      bodyFont: "Manrope",
      colors: ["#10b981", "#ffffff", "#0b0a1a"],
      description: "Deep space background with radial aurora green flows, subtle glow borders, and futuristic dark typography.",
      previewStyles: {
        background: "#0b0a1a",
        color: "#ffffff",
        border: "1px solid rgba(16, 185, 129, 0.3)",
        borderRadius: "1rem",
        boxShadow: "0 0 15px rgba(16, 185, 129, 0.15)",
        fontFamily: "'Manrope', sans-serif"
      },
      previewBadge: "bg-[rgba(16,185,129,0.15)] text-[#10b981]"
    },
    {
      id: "editorial",
      name: "Classic Editorial",
      keywords: ["elegant", "warm", "literary"],
      headingFont: "Playfair Display",
      bodyFont: "Inter",
      colors: ["#15803d", "#1c1917", "#fdfbf7"],
      description: "An elegant serif-led, bookish design on warm cream backgrounds with forest green accents and fine paper-like borders.",
      previewStyles: {
        background: "#fdfbf7",
        color: "#1c1917",
        border: "1px solid #e5e2dc",
        borderRadius: "0.25rem",
        boxShadow: "0 2px 4px rgba(0, 0, 0, 0.01)",
        fontFamily: "'Inter', sans-serif"
      },
      previewBadge: "bg-[#f0fdf4] text-[#15803d]"
    },
    {
      id: "cyberpunk",
      name: "Cyberpunk Neon",
      keywords: ["neon-pink", "cyan", "sci-fi"],
      headingFont: "Orbitron",
      bodyFont: "Fira Code",
      colors: ["#00ffff", "#ff007f", "#0d0e12"],
      description: "Futuristic neon cyberpunk theme, intense glowing border lines, high-contrast cyan, hot pink, and pitch black.",
      previewStyles: {
        background: "#0d0e12",
        color: "#00ffff",
        border: "1px solid #ff007f",
        borderRadius: "0.5rem",
        boxShadow: "0 0 10px rgba(255, 0, 127, 0.3)",
        fontFamily: "'Fira Code', monospace"
      },
      previewBadge: "bg-[rgba(0,255,255,0.1)] text-[#00ffff] font-mono text-xs"
    },
    {
      id: "organic",
      name: "Earth & Sage Calm",
      keywords: ["earth-toned", "wellness", "natural"],
      headingFont: "Lora",
      bodyFont: "Raleway",
      colors: ["#78716c", "#2d1e14", "#f5efeb"],
      description: "A calming organic theme featuring natural warm stones, terracotta hints, sage accents, and round cozy containers.",
      previewStyles: {
        background: "#ffffff",
        color: "#2d1e14",
        border: "1px solid #ded5cc",
        borderRadius: "1.25rem",
        boxShadow: "0 4px 10px rgba(45, 30, 20, 0.04)",
        fontFamily: "'Raleway', sans-serif"
      },
      previewBadge: "bg-[#f5f5f4] text-[#78716c]"
    }
  ];

  const handleApplyTheme = (themeId) => {
    localStorage.setItem("faculty-theme", themeId);
    setCurrentTheme(themeId);
    applyThemeFonts(themeId);
    
    // Dispatch event to inform FacultyDashboard and other views
    window.dispatchEvent(new Event("faculty-theme-change"));

    setSaveSuccess(true);
    setTimeout(() => {
      setSaveSuccess(false);
    }, 3000);
  };

  useEffect(() => {
    // Make sure correct fonts are loaded for active theme on settings page load
    applyThemeFonts(currentTheme);
  }, [currentTheme]);

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
      <div className="p-6 border-b border-gray-200 flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
            <Palette className="w-5 h-5 text-emerald-600" />
            Theme & Style Preferences
          </h2>
          <p className="text-gray-500 text-sm mt-1">
            Choose a visual design preset to transform the entire layout, typography, borders, and color scheme of your Faculty Portal.
          </p>
        </div>
        {saveSuccess && (
          <div className="flex items-center gap-1.5 px-3 py-1 bg-emerald-50 text-emerald-700 text-sm font-medium rounded-full animate-fade-in">
            <Check className="w-4 h-4" />
            Applied Successfully
          </div>
        )}
      </div>

      <div className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {stylePresets.map((preset) => {
            const isActive = currentTheme === preset.id;
            
            return (
              <div 
                key={preset.id}
                className={`border rounded-xl p-5 flex flex-col justify-between transition-all duration-300 ${
                  isActive 
                    ? "border-emerald-500 ring-2 ring-emerald-500/20 bg-emerald-50/10" 
                    : "border-gray-200 hover:border-gray-300 hover:shadow-md bg-white"
                }`}
              >
                <div>
                  {/* Presets Header */}
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <div>
                      <h3 className="font-semibold text-gray-900 flex items-center gap-2">
                        {preset.name}
                        {isActive && <Check className="w-4 h-4 text-emerald-600 flex-shrink-0" />}
                      </h3>
                      {/* Keywords Badges */}
                      <div className="flex flex-wrap gap-1 mt-1">
                        {preset.keywords.map(kw => (
                          <span key={kw} className="text-[10px] px-1.5 py-0.5 rounded bg-gray-100 text-gray-600 font-medium">
                            {kw}
                          </span>
                        ))}
                      </div>
                    </div>
                    {/* Theme Swatches */}
                    <div className="flex items-center gap-1 bg-gray-50 p-1 rounded-md border border-gray-100 flex-shrink-0">
                      {preset.colors.map((c, i) => (
                        <div 
                          key={i} 
                          className="w-3.5 h-3.5 rounded-full border border-gray-200 shadow-sm"
                          style={{ backgroundColor: c }}
                          title={`Color swatch ${i+1}`}
                        />
                      ))}
                    </div>
                  </div>

                  <p className="text-xs text-gray-500 mb-4 h-10 overflow-hidden leading-relaxed">
                    {preset.description}
                  </p>

                  {/* Realtime Style Preview Box */}
                  <div 
                    className="p-3.5 rounded-lg border mb-4 text-xs relative overflow-hidden transition-all duration-300"
                    style={{
                      ...preset.previewStyles,
                      minHeight: "95px",
                      display: "flex",
                      flexDirection: "column",
                      justifyContent: "space-between"
                    }}
                  >
                    {/* Mini card structure to showcase theme properties */}
                    <div className="flex items-center justify-between border-b pb-1.5 mb-1.5" style={{ borderColor: preset.previewStyles.border || "rgba(0,0,0,0.1)" }}>
                      <span className="font-semibold" style={{ fontFamily: `'${preset.headingFont}', sans-serif` }}>
                        Analytics Preview
                      </span>
                      <span className={`text-[9px] px-1 rounded-full font-medium ${preset.previewBadge}`}>
                        +14%
                      </span>
                    </div>

                    <div className="flex items-baseline justify-between">
                      <div>
                        <div className="text-lg font-bold" style={{ fontFamily: `'${preset.headingFont}', sans-serif` }}>
                          14,204
                        </div>
                        <div className="text-[9px] opacity-80" style={{ fontFamily: `'${preset.bodyFont}', sans-serif` }}>
                          Total unique student views
                        </div>
                      </div>
                      <Eye className="w-5 h-5 opacity-70" />
                    </div>
                  </div>

                  {/* Font pairings indicator */}
                  <div className="text-[11px] text-gray-500 flex items-center gap-1.5 border-t border-gray-100 pt-3 mt-3">
                    <span className="font-semibold text-gray-700">Typography:</span>
                    <span className="font-mono text-[10px] bg-gray-50 px-1.5 py-0.5 rounded border border-gray-100">
                      H: {preset.headingFont} + B: {preset.bodyFont}
                    </span>
                  </div>
                </div>

                {/* Apply CTA */}
                <button
                  type="button"
                  onClick={() => handleApplyTheme(preset.id)}
                  disabled={isActive}
                  className={`mt-4 w-full flex items-center justify-center gap-2 py-2 text-xs font-semibold rounded-lg transition-all ${
                    isActive 
                      ? "bg-emerald-100 text-emerald-800 cursor-default" 
                      : "bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm active:scale-95"
                  }`}
                >
                  {isActive ? (
                    <>
                      <Check className="w-3.5 h-3.5" />
                      Active Theme
                    </>
                  ) : (
                    <>
                      <Palette className="w-3.5 h-3.5" />
                      Apply Theme
                    </>
                  )}
                </button>
              </div>
            );
          })}
        </div>

        {/* Accessiblity Callout */}
        <div className="mt-8 p-4 bg-amber-50 rounded-xl border border-amber-100 flex gap-3 text-amber-900 text-sm">
          <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold">Note on accessibility:</span> presets like Claymorphism, Retro Brutalism, and Cyberpunk use highly stylized visual elements. If you require standard high-contrast, approach-friendly setups, we recommend sticking to <strong className="font-bold">Default Emerald</strong> or <strong className="font-bold">Minimalist Swiss</strong>.
          </div>
        </div>
      </div>
    </div>
  );
};

export default StyleSettings;
