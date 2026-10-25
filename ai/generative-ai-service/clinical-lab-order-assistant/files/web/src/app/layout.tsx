import type { Metadata } from "next";
import { Plus_Jakarta_Sans, JetBrains_Mono, IBM_Plex_Sans_Arabic } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/providers";

const sans = Plus_Jakarta_Sans({ variable: "--font-sans-base", subsets: ["latin"], display: "swap" });
const mono = JetBrains_Mono({ variable: "--font-mono-base", subsets: ["latin"], display: "swap" });
const arabic = IBM_Plex_Sans_Arabic({ variable: "--font-arabic", subsets: ["arabic"], weight: ["400", "500", "600", "700"], display: "swap" });

export const metadata: Metadata = {
  title: "LabSense · Every test, justified",
  description: "Lab-ordering assistant that avoids redundant blood tests, running on a dedicated OCI Generative AI model.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" suppressHydrationWarning className={`${sans.variable} ${mono.variable} ${arabic.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col"><Providers>{children}</Providers></body>
    </html>
  );
}
