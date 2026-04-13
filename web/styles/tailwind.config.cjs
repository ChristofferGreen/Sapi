/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./sapi/build/**/*.py",
    "./scripts/**/*.py",
    "./tests/**/*.py",
    "./web/styles/**/*.css",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
};
