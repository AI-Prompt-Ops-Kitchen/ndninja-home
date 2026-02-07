import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.promptkit.app',
  appName: 'PromptKit',
  webDir: 'out', // Next.js static export directory
  server: {
    // In development, point to your Next.js dev server
    // url: 'http://localhost:3000',
    // cleartext: true,
    androidScheme: 'https',
  },
  plugins: {
    SplashScreen: {
      launchAutoHide: true,
      backgroundColor: '#0a0a0f',
      showSpinner: false,
    },
  },
};

export default config;
