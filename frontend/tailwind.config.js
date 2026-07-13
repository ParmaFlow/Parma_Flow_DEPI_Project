/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"]
      },
      colors: {
        ink: "#15202b",
        clinical: "#0080FF", // Logo primary blue
        signal: "#b45309"
      }
    }
  },
  plugins: []
};

