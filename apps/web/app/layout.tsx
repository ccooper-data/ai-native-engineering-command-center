import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI-Native Engineering Command Center",
  description: "Human-governed multi-agent software engineering orchestration",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
