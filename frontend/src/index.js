import React from 'react';
import ReactDOM from 'react-dom/client';
import { ChakraProvider, extendTheme, ColorModeScript } from '@chakra-ui/react';
import App from './App';
import './index.css';

// Glassmorphism Theme
const theme = extendTheme({
  fonts: {
    heading: "'Audiowide', sans-serif",
    body: "'Exo 2', sans-serif",
    mono: "'Exo 2', monospace",
  },
  colors: {
    brand: {
      50: '#eef2ff',
      100: '#e0e7ff',
      200: '#c7d2fe',
      300: '#a5b4fc',
      400: '#818cf8',
      500: '#6366f1',
      600: '#4f46e5',
      700: '#4338ca',
      800: '#3730a3',
      900: '#312e81',
    },
  },
  config: {
    initialColorMode: 'dark',
    useSystemColorMode: false,
  },
  styles: {
    global: (props) => ({
      body: {
        bg: props.colorMode === 'dark'
          ? 'linear-gradient(135deg, #0f172a, #1e293b, #312e81)'
          : 'linear-gradient(135deg, #f0f9ff, #e0f2fe, #dbeafe)',
        color: props.colorMode === 'dark' ? '#ffffff' : '#1e293b',
      },
      '*': {
        transition: 'all 300ms ease-in-out',
      },
    }),
  },
  components: {
    Button: {
      baseStyle: (props) => ({
        backdropFilter: 'blur(12px)',
        background: props.colorMode === 'dark' ? 'rgba(100,200,255,0.08)' : 'rgba(255,255,255,0.7)',
        border: '1px solid',
        borderColor: props.colorMode === 'dark' ? 'rgba(100,200,255,0.25)' : 'rgba(100,116,139,0.2)',
        borderRadius: '16px',
        boxShadow: '0 4px 16px rgba(0,0,0,0.2)',
        transition: 'all 300ms ease-in-out',
        color: props.colorMode === 'dark' ? '#ffffff' : '#1e293b',
        _hover: {
          transform: 'translateY(-2px)',
          background: props.colorMode === 'dark' ? 'rgba(100,200,255,0.15)' : 'rgba(255,255,255,0.9)',
          boxShadow: '0 6px 20px rgba(100,200,255,0.2)',
          borderColor: props.colorMode === 'dark' ? 'rgba(100,200,255,0.4)' : 'rgba(100,116,139,0.3)',
        },
        _active: {
          transform: 'translateY(0)',
        },
      }),
    },
    Text: {
      baseStyle: (props) => ({
        color: props.colorMode === 'dark' ? '#ffffff' : '#1e293b',
      }),
    },
    Box: {
      baseStyle: {
        transition: 'all 300ms ease-in-out',
      },
    },
    Card: {
      baseStyle: (props) => ({
        backdropFilter: 'blur(12px)',
        background: props.colorMode === 'dark' ? 'rgba(100,200,255,0.08)' : 'rgba(255,255,255,0.7)',
        border: '1px solid',
        borderColor: props.colorMode === 'dark' ? 'rgba(100,200,255,0.25)' : 'rgba(100,116,139,0.2)',
        borderRadius: '20px',
        boxShadow: '0 8px 32px rgba(0,0,0,0.25)',
        transition: 'all 300ms ease-in-out',
        color: props.colorMode === 'dark' ? '#ffffff' : '#1e293b',
        _hover: {
          transform: 'translateY(-2px)',
          boxShadow: '0 12px 40px rgba(100,200,255,0.15)',
          borderColor: props.colorMode === 'dark' ? 'rgba(100,200,255,0.35)' : 'rgba(100,116,139,0.3)',
        },
      }),
    },
    Tabs: {
      baseStyle: (props) => ({
        tab: {
          transition: 'all 300ms ease-in-out',
          color: props.colorMode === 'dark' ? 'rgba(255,255,255,0.6)' : 'rgba(30,41,59,0.7)',
          _selected: {
            color: props.colorMode === 'dark' ? '#818cf8' : '#4338ca',
            borderColor: props.colorMode === 'dark' ? '#818cf8' : '#4338ca',
            background: props.colorMode === 'dark' ? 'rgba(129,140,248,0.1)' : 'rgba(129,140,248,0.15)',
          },
          _hover: {
            color: props.colorMode === 'dark' ? '#a5b4fc' : '#4338ca',
            background: props.colorMode === 'dark' ? 'rgba(165,180,252,0.05)' : 'rgba(165,180,252,0.1)',
          },
        },
      }),
    },
  },
});

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <>
    <ColorModeScript initialColorMode={theme.config.initialColorMode} />
    <ChakraProvider theme={theme}>
      <App />
    </ChakraProvider>
  </>
);
