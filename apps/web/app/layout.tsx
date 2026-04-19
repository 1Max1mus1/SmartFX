import "./globals.css";
import type { Metadata } from "next";
import { Plus_Jakarta_Sans, Noto_Sans_SC } from "next/font/google";
import type { ReactNode } from "react";

const jakarta = Plus_Jakarta_Sans({
  subsets: ["latin"],
  variable: "--font-jakarta"
});

const noto = Noto_Sans_SC({
  subsets: ["latin"],
  variable: "--font-noto"
});

export const metadata: Metadata = {
  title: "SmartFX",
  description: "AI-assisted foreign exchange reference platform"
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="zh-CN">
      <body className={`${jakarta.variable} ${noto.variable}`}>{children}</body>
    </html>
  );
}

