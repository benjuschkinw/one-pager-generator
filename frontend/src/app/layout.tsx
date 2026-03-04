import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "M&A One-Pager Generator | Constellation Capital AG",
  description: "AI-powered One-Pager slide generation for M&A deal analysis",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="min-h-screen bg-cc-surface font-sans antialiased">
        <header className="bg-cc-dark border-b border-cc-navy">
          <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              {/* CC monogram */}
              <div className="w-9 h-9 rounded bg-white/10 flex items-center justify-center">
                <span className="text-white font-bold text-sm tracking-tight">CC</span>
              </div>
              <div>
                <h1 className="text-white text-base font-semibold tracking-tight leading-tight">
                  Constellation Capital AG
                </h1>
                <p className="text-cc-light/70 text-xs font-medium">
                  One-Pager Generator
                </p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <a
                href="/jobs"
                className="text-xs text-cc-light/60 hover:text-white font-medium transition-colors"
              >
                Jobs
              </a>
              <span className="text-xs text-cc-light/50 font-medium">
                M&A Deal Tools
              </span>
            </div>
          </div>
        </header>
        <main className="max-w-7xl mx-auto px-6 py-8">{children}</main>
      </body>
    </html>
  );
}
