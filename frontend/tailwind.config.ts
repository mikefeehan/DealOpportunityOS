import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "#070707",
        panel: "#101010",
        panel2: "#161616",
        border: "#2b2b2b",
        muted: "#a1a0a0", // InTrust brand grey (PMS 422)
        ink: "#f4f4f2",
        // Accent maps to InTrust brand blue (PMS 7706 #12648a), brightened for
        // legibility on the near-black UI. `brand` keeps the exact brand value.
        amber: "#2f93c4",
        brand: "#12648a",
        cyan: "#3dd6c6",
        green: "#86e07b",
        red: "#ff6b5f"
      },
      fontFamily: {
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
        display: ["var(--font-display)", "var(--font-sans)", "sans-serif"]
      },
      boxShadow: {
        terminal: "0 0 0 1px rgba(47,147,196,0.16), 0 24px 70px rgba(0,0,0,0.44)"
      }
    }
  },
  plugins: []
};

export default config;
