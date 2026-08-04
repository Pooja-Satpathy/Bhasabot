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
          900: "var(--bg-surface-900)",
          800: "var(--bg-surface-800)",
          700: "var(--bg-surface-700)",
          600: "var(--bg-surface-600)",
          500: "var(--bg-surface-500)",
        },
        slate: {
          50: "var(--slate-50)",
          100: "var(--slate-100)",
          200: "var(--slate-200)",
          300: "var(--slate-300)",
          400: "var(--slate-400)",
          500: "var(--slate-500)",
          600: "var(--slate-600)",
          700: "var(--slate-700)",
          800: "var(--slate-800)",
          900: "var(--slate-900)",
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
