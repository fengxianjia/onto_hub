/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{vue,js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                background: '#FAFAFA',
                foreground: '#0F172A',
                muted: '#F1F5F9',
                'muted-foreground': '#64748B',
                accent: '#0052FF',
                'accent-secondary': '#4D7CFF',
                'accent-foreground': '#FFFFFF',
                border: '#E2E8F0',
                card: '#FFFFFF',
                ring: '#0052FF',
            },
            fontFamily: {
                sans: ['Inter', 'system-ui', 'sans-serif'],
                display: ['Calistoga', 'Georgia', 'serif'],
                mono: ['JetBrains Mono', 'monospace'],
            },
            fontSize: {
                'hero': ['5.25rem', { lineHeight: '1.05', letterSpacing: '-0.02em' }],
                'section': ['3.25rem', { lineHeight: '1.15' }],
            },
            boxShadow: {
                'accent': '0 4px 14px rgba(0, 82, 255, 0.25)',
                'accent-lg': '0 8px 24px rgba(0, 82, 255, 0.35)',
            },
            animation: {
                'float': 'float 5s ease-in-out infinite',
                'float-delayed': 'float 4s ease-in-out infinite',
                'pulse-dot': 'pulse-dot 2s ease-in-out infinite',
                'spin-slow': 'spin 60s linear infinite',
            },
            keyframes: {
                float: {
                    '0%, 100%': { transform: 'translateY(0)' },
                    '50%': { transform: 'translateY(-10px)' },
                },
                'pulse-dot': {
                    '0%, 100%': { transform: 'scale(1)', opacity: '1' },
                    '50%': { transform: 'scale(1.3)', opacity: '0.7' },
                },
            },
        },
    },
    plugins: [],
}
