/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          purple: '#5E3A85',
          purpleDark: '#3F2460',
          purpleData: '#7B4FA8',
          purpleLight: '#F1ECF7',
          purpleLine: '#D9CEE8',
          lime: '#B4C805',
          limeText: '#7E9A0A',
          limeLight: '#F3F7D9',
          limeData: '#7E9A0A',
        },
        ink: { DEFAULT: '#222222', muted: '#666666', faint: '#999999' },
        line: '#E5E0EC',
        surface: '#FFFFFF',
        tag: {
          baixar: '#FDE2E1',
          subir: '#DCEFD9',
          manter: '#EEEEEE',
          revisar: '#FFF2CC',
          riscoBaixo: '#DCEFD9',
          riscoMedio: '#FFF2CC',
          riscoAlto: '#FDE2E1',
        },
        zebra: '#FAF8FC',
        decided: '#F4F4F4',
      },
      fontFamily: { sans: ['Inter', 'DejaVu Sans', 'Arial', 'sans-serif'] },
      borderRadius: { card: '6px' },
    },
  },
  plugins: [],
}
