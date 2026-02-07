'use client';

import Link from 'next/link';
import { motion } from 'framer-motion';
import { Sparkles, Github, Twitter } from 'lucide-react';

const footerLinks = {
  Product: [
    { label: 'Browse Prompts', href: '/browse' },
    { label: 'Pricing', href: '/pricing' },
    { label: 'Changelog', href: '#' },
    { label: 'Roadmap', href: '#' },
  ],
  Resources: [
    { label: 'Documentation', href: '#' },
    { label: 'Blog', href: '#' },
    { label: 'Prompt Engineering Guide', href: '#' },
    { label: 'API Reference', href: '#' },
  ],
  Company: [
    { label: 'About', href: '/about' },
    { label: 'Careers', href: '#' },
    { label: 'Privacy Policy', href: '#' },
    { label: 'Terms of Service', href: '#' },
  ],
};

export function Footer() {
  return (
    <footer className="border-t border-gray-800 bg-gray-950 relative overflow-hidden">
      {/* Subtle mesh gradient */}
      <div className="absolute inset-0 opacity-30">
        <div className="absolute bottom-0 left-1/4 w-96 h-96 bg-indigo-600/5 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-purple-600/5 rounded-full blur-3xl" />
      </div>

      <div className="relative mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-8">
          {/* Brand */}
          <div className="col-span-2">
            <Link href="/" className="flex items-center gap-2.5 mb-4">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-600 to-purple-600">
                <Sparkles className="h-4 w-4 text-white" />
              </div>
              <span className="text-lg font-bold text-white">
                Prompt<span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400">Kit</span>
              </span>
            </Link>
            <p className="text-sm text-gray-500 max-w-xs mb-6 leading-relaxed">
              The definitive toolkit for crafting better AI prompts. Used by thousands of professionals worldwide.
            </p>
            <div className="flex items-center gap-3">
              <a href="#" className="p-2 rounded-lg bg-gray-800/50 text-gray-400 hover:text-white hover:bg-gray-800 transition-all duration-200">
                <Twitter className="h-4 w-4" />
              </a>
              <a href="#" className="p-2 rounded-lg bg-gray-800/50 text-gray-400 hover:text-white hover:bg-gray-800 transition-all duration-200">
                <Github className="h-4 w-4" />
              </a>
            </div>
          </div>

          {/* Link columns */}
          {Object.entries(footerLinks).map(([title, links]) => (
            <div key={title}>
              <h3 className="text-sm font-semibold text-gray-300 mb-4">{title}</h3>
              <ul className="space-y-2.5">
                {links.map((link) => (
                  <li key={link.label}>
                    <Link
                      href={link.href}
                      className="text-sm text-gray-500 hover:text-gray-300 transition-colors"
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Bottom */}
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="mt-12 pt-8 border-t border-gray-800 flex flex-col sm:flex-row items-center justify-between gap-4"
        >
          <p className="text-sm text-gray-600">
            © {new Date().getFullYear()} PromptKit. All rights reserved.
          </p>
          <p className="text-xs text-gray-700">
            Built with ❤️ for prompt engineers everywhere
          </p>
        </motion.div>
      </div>
    </footer>
  );
}
