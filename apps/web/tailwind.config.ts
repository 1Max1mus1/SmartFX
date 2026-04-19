import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        jade: {
          500: "#2FB36C",
          600: "#179356"
        },
        gold: {
          200: "#F8EFCF",
          300: "#F2D98B",
          500: "#E7C36A"
        },
        ink: "#111111",
        mist: "#F6F7F4"
      },
      boxShadow: {
        soft: "0 24px 60px rgba(17, 17, 17, 0.08)"
      },
      borderRadius: {
        panel: "28px"
      }
    }
  },
  plugins: []
};

export default config;

