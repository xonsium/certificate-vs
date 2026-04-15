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
          primary: "#2563EB",
          "primary-content": "#FFFFFF",
          secondary: "#6B7280",
          "secondary-content": "#FFFFFF",
          accent: "#2563EB",
          neutral: "#1F2937",
          "base-100": "#FFFFFF",
          "base-200": "#F3F4F6",
          "base-300": "#E5E7EB",
          "base-content": "#1F2937",
          info: "#2563EB",
          success: "#10B981",
          warning: "#F59E0B",
          error: "#EF4444",
        },
      },
    ],
  },
};
