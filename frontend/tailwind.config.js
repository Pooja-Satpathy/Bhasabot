/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}", "./public/index.html"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#f0f4ff", 100: "#e0e9ff", 200: "#c7d4ff", 300: "#a4b5ff",
          400: "#7a8ef5", 500: "#5b6fea", 600: "#4455d8", 700: "#3642be",
          800: "#2d369a", 900: "#28317a",
        },
        surface: {
          900: "#0d0f1a", 800: "#141626", 700: "#1c1f35",
          600: "#242843", 500: "#2d3150",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      keyframes: {
        "slide-in-up": {
          "0%": { transform: "translateY(12px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" },
        },
        "fade-in": { "0%": { opacity: "0" }, "100%": { opacity: "1" } },
        "pulse-glow": {
          "0%, 100%": { boxShadow: "0 0 8px rgba(91, 111, 234, 0.3)" },
          "50%": { boxShadow: "0 0 20px rgba(91, 111, 234, 0.7)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
      },
      animation: {
        "slide-in-up": "slide-in-up 0.3s ease-out",
        "fade-in": "fade-in 0.4s ease-out",
        "pulse-glow": "pulse-glow 2s infinite",
        shimmer: "shimmer 1.5s infinite linear",
      },
    },
  },
  plugins: [],
};
