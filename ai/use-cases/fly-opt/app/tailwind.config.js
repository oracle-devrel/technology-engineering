/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Legacy NVIDIA colors (kept for gradual migration)
        'nvidia-green': '#76B900',
        'nvidia-light': '#8ED100',
        'nvidia-dark': '#5A8F00',
        nvidia: {
          green: '#76B900',
          'green-dark': '#5A8F00',
          'green-light': '#8ED100',
        },
        // OCI Brand Colors
        oracle: {
          red: '#C74634',
          'red-dark': '#A63D2D',
          'red-light': '#E55D4A',
          'red-hover': '#B33D2B',
        },
        oci: {
          blue: '#0066CC',
          'blue-dark': '#004C99',
          'blue-light': '#3399FF',
          teal: '#00758F',
          green: '#1A8917',
        },
        dark: {
          bg: '#0D1117',
          card: '#1B1F2E',
          border: '#2D3748',
          hover: '#252D3D',
        },
        navy: {
          DEFAULT: '#003A75',
          dark: '#002855',
          light: '#0052A5',
        },
        accent: {
          blue: '#006BBF',
          'blue-light': '#0088F0',
        },
      },
      fontFamily: {
        mono: ['IBM Plex Mono', 'monospace'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'count-up': 'countUp 1s ease-out forwards',
        'slide-in': 'slideIn 0.3s ease-out',
        'fade-in': 'fadeIn 0.3s ease-out',
      },
      keyframes: {
        countUp: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideIn: {
          '0%': { opacity: '0', transform: 'translateX(-10px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
      },
      backdropBlur: {
        xs: '2px',
      },
    },
  },
  plugins: [],
}
