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
      <body className="min-h-screen bg-slate-50">
        <header className="bg-cc-dark text-white py-4 px-6 shadow-md">
          <div className="max-w-7xl mx-auto flex items-center justify-between">
            <div>
              <h1 className="text-xl font-bold tracking-tight">
                Constellation Capital AG
              </h1>
              <p className="text-sm text-cc-light opacity-80">
                M&A One-Pager Generator
              </p>
            </div>
          </div>
        </header>
        <main className="max-w-7xl mx-auto px-6 py-8">{children}</main>
      </body>
    </html>
  );
}
