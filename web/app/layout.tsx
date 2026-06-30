import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ssr1 Movies",
  description: "100 classic movies scraped from ssr1.scrape.center",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh">
      <body className="min-h-screen bg-neutral-950 text-neutral-100 antialiased">
        {children}
      </body>
    </html>
  );
}
