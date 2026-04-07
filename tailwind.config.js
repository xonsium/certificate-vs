/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/templates/**/*.html", "./app/static/**/*.js"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      colors: {
        brand: {
          primary: "var(--color-primary)",
          bgdark: "var(--color-background-dark)",
          surfacedark: "var(--color-surface-dark)",
          muted: "var(--color-text-muted)",
          bglight: "var(--color-background-light)",
        },
      },
    },
  },
  plugins: [require("daisyui")],
  daisyui: {
    themes: [
      {
        cert: {
          primary: "#20268C",
          "primary-content": "#F2EFEB",
          secondary: "#363740",
          "secondary-content": "#F2EFEB",
          accent: "#9798A6",
          neutral: "#171826",
          "base-100": "#F2EFEB",
          "base-200": "#e8e4df",
          "base-300": "#d4d0cb",
          "base-content": "#171826",
          info: "#20268C",
          success: "#2d6a4f",
          warning: "#d4a017",
          error: "#9b2335",
        },
      },
    ],
  },
};
