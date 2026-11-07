/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#070b14",
        charcoal: "#101726",
        navy: "#162033",
        mist: "#9aa8c7",
      },
      fontFamily: {
        sans: ["Outfit", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      boxShadow: {
        glow: "0 0 80px rgba(96, 80, 255, 0.18)",
      },
    },
  },
  plugins: [],
};
