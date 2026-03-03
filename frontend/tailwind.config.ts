import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        "cc-dark": "#1F4E79",
        "cc-mid": "#2E75B6",
        "cc-light": "#BDD7EE",
        "cc-accent": "#5B9BD5",
      },
    },
  },
  plugins: [],
};

export default config;
