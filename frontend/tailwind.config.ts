import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        sidebar: {
          DEFAULT: "#0f172a",
          hover: "#1e293b",
          active: "#1d4ed8",
          text: "#94a3b8",
          "text-active": "#ffffff",
        },
        primary: {
          DEFAULT: "#2563eb",
          hover: "#1d4ed8",
          foreground: "#ffffff",
        },
        danger: {
          DEFAULT: "#dc2626",
          hover: "#b91c1c",
          foreground: "#ffffff",
        },
        surface: {
          DEFAULT: "#ffffff",
          2: "#f8fafc",
          3: "#f1f5f9",
        },
        border: {
          DEFAULT: "#e2e8f0",
          strong: "#cbd5e1",
        },
        muted: "#64748b",
        status: {
          open: "#2563eb",
          in_progress: "#d97706",
          resolved: "#16a34a",
          pending: "#7c3aed",
        },
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
