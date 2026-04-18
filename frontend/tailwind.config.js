/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: "#1E40AF",
        success: "#15803D",
        warning: "#B45309",
        danger: "#B91C1C",
        muted: "#6B7280",
        surface: "#F9FAFB",
        border: "#E5E7EB"
      },
      boxShadow: {
        panel: "0 18px 45px -24px rgba(15, 23, 42, 0.35)"
      },
      fontFamily: {
        sans: ["Trebuchet MS", "Segoe UI", "sans-serif"],
        display: ["Georgia", "Cambria", "serif"]
      }
    }
  },
  plugins: []
};
