import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Powerloom Manufacturing Digital Twin — HAL",
  description: "5-Department Factory Digital Twin: Component Tracking, Capacity Intelligence, Load Balancing & Prediction",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" style={{ background: "#0a0c0f" }}>
      <head>
        <link
          rel="preconnect"
          href="https://fonts.googleapis.com"
        />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Sora:wght@300;400;600&display=swap"
          rel="stylesheet"
        />
      </head>
      <body style={{ margin: 0, background: "#0a0c0f", color: "#e0e8f0" }}>
        {children}
      </body>
    </html>
  );
}
