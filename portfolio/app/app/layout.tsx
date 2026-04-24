import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Jorg — AI & Full-Stack Engineer",
  description: "Building AI systems, trading bots, and full-stack applications. Personal portfolio of Jorg.",
  openGraph: {
    title: "Jorg — AI & Full-Stack Engineer",
    description: "Building AI systems, trading bots, and full-stack applications.",
    type: "website",
    url: "https://portfolio.mybrain.world",
    images: [
      {
        url: "/images/og-image.png",
        width: 1200,
        height: 630,
        alt: "Jorg — AI & Full-Stack Engineer",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Jorg — AI & Full-Stack Engineer",
    description: "Building AI systems, trading bots, and full-stack applications.",
    images: ["/images/og-image.png"],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
