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
  plugins: [],
};
