export const fontsMap = {
  default: "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap",
  glassmorphism: "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;500;600;700&display=swap",
  claymorphism: "https://fonts.googleapis.com/css2?family=Fredoka:wght@400;500;600;700&family=Nunito:wght@300;400;500;600;700&display=swap",
  minimalism: "https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@300;400;500;600;700&display=swap",
  bentogrid: "https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&family=DM+Sans:wght@400;500;700&display=swap",
  neumorphism: "https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&family=Open+Sans:wght@300;400;500;600;700&display=swap",
  brutalism: "https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=JetBrains+Mono:wght@400;500;700&display=swap",
  aurora: "https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=Manrope:wght@300;400;500;600;700&display=swap",
  editorial: "https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400..700;1,400..700&family=Inter:wght@300;400;500;600;700&display=swap",
  cyberpunk: "https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;700;900&family=Fira+Code:wght@400;500;700&display=swap",
  organic: "https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400..700;1,400..700&family=Raleway:wght@300;400;500;600;700&display=swap"
};

export const applyThemeFonts = (themeKey) => {
  const fontUrl = fontsMap[themeKey];
  if (!fontUrl) return;
  
  let linkEl = document.getElementById("theme-google-fonts");
  if (!linkEl) {
    linkEl = document.createElement("link");
    linkEl.id = "theme-google-fonts";
    linkEl.rel = "stylesheet";
    document.head.appendChild(linkEl);
  }
  linkEl.href = fontUrl;
};
