import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        "cc-dark": "#1F4E79",
        "cc-navy": "#223F6A",
        "cc-mid": "#2E75B6",
        "cc-light": "#BDD7EE",
        "cc-accent": "#5B9BD5",
        "cc-surface": "#F0F5FA",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
