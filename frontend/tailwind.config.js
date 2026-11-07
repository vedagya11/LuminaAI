/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#101114",
        panel: "#17191E",
        card: "#1C1F25",
        line: "#2B2E36",
        ink: "#F5F5F5",
        muted: "#9A9DA7",
        accent: "#8B7CF6",
        success: "#42B883",
        danger: "#EF6461",
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      boxShadow: {
        card: "0 1px 2px rgba(0, 0, 0, 0.28)",
      },
    },
  },
  plugins: [],
};
