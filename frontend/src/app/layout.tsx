import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ForensicGuard — Secure Erasure & Recovery Platform",
  description: "Integrated secure data erasure and forensic file recovery",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-ink font-display text-gray-100">{children}</body>
    </html>
  );
}
