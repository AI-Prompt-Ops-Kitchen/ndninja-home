import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
});

export const metadata: Metadata = {
  title: 'PromptKit — AI Prompt Toolkit',
  description:
    'The definitive toolkit for crafting better AI prompts. Browse, customize, and deploy battle-tested prompts for ChatGPT, Claude, Gemini, and more.',
  keywords: ['AI prompts', 'prompt engineering', 'ChatGPT', 'Claude', 'prompt templates'],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.variable} font-sans antialiased bg-gray-950 text-gray-100`}>
        {children}
      </body>
    </html>
  );
}
