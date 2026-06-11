import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "#070707",
        panel: "#101010",
        panel2: "#151515",
        border: "#2b2b2b",
        muted: "#8d939c",
        ink: "#f4f4f2",
        amber: "#e3b341",
        cyan: "#3dd6c6",
        green: "#86e07b",
        red: "#ff6b5f"
      },
      boxShadow: {
        terminal: "0 0 0 1px rgba(227,179,65,0.14), 0 24px 70px rgba(0,0,0,0.44)"
      }
    }
  },
  plugins: []
};

export default config;
