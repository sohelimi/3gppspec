import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "3gppSpec — 3GPP AI Assistant",
  description: "Ask anything about 3GPP telecommunications standards. Powered by AI.",
  icons: { icon: "/favicon.ico" },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-slate-950 text-slate-100 antialiased">
        {children}
      </body>
    </html>
  );
}
