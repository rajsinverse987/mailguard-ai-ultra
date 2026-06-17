import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "MailGuard AI Ultra",
  description: "AI email intelligence + WhatsApp voice assistant",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
