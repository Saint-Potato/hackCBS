/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        vscode: {
          bg: '#1e1e1e',
          sidebar: '#333333',
          panel: '#252526',
          surface: '#2d2d30',
          border: '#3e3e42',
          primary: '#3794ff',
          secondary: '#f48fb1',
          success: '#4ec9b0',
          error: '#f48771',
          warning: '#dcdcaa',
          text: {
            primary: '#cccccc',
            secondary: '#969696',
          },
          hover: 'rgba(255, 255, 255, 0.05)',
          selected: 'rgba(55, 148, 255, 0.15)',
        },
      },
      fontFamily: {
        sans: ['"Segoe UI"', 'Ubuntu', 'Roboto', 'Helvetica', 'Arial', 'sans-serif'],
        mono: ['Consolas', 'Monaco', '"Courier New"', 'monospace'],
      },
    },
  },
  plugins: [],
}