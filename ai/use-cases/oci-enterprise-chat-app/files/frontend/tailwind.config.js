/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        oracle: {
          red: '#C74634',
          'red-dark': '#A63D2D',
          'red-light': '#E55D4A',
        },
        oci: {
          blue: '#0066CC',
          'blue-dark': '#004C99',
        },
        dark: {
          900: '#0D1117',
          800: '#161B22',
          700: '#1B1F2E',
          600: '#252D3D',
          500: '#2D3748',
          400: '#4A5568',
          300: '#A0AEC0',
          200: '#CBD5E0',
          100: '#E2E8F0',
          bg: '#0D1117',
          card: '#1B1F2E',
          hover: '#252D3D',
          border: '#2D3748',
        },
        confidence: {
          high: '#22C55E',
          medium: '#EAB308',
          low: '#EF4444',
        },
        status: {
          pending: '#6B7280',
          confirmed: '#22C55E',
          rejected: '#EF4444',
          review: '#3B82F6',
        },
      },
      fontFamily: {
        sans: ['"Oracle Sans"', 'Oracle Sans', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', 'sans-serif'],
      },
      boxShadow: {
        'oracle': '0 4px 14px 0 rgba(199, 70, 52, 0.25)',
        'card': '0 2px 8px rgba(0, 0, 0, 0.4)',
        'modal': '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'spin-slow': 'spin 2s linear infinite',
      },
    },
  },
  plugins: [],
}
