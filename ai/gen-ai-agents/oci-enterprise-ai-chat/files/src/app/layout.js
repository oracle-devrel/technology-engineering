import { AppRouterCacheProvider } from "@mui/material-nextjs/v15-appRouter";
import { ThemeProvider } from "@mui/material/styles";
import { Exo_2, Roboto } from "next/font/google";
import localFont from "next/font/local";
import "./globals.css";
import theme from "./theme/theme";

const roboto = Roboto({
  weight: ["300", "400", "500", "700"],
  subsets: ["latin"],
  display: "swap",
  variable: "--font-roboto",
});

const exo2 = Exo_2({
  weight: ["300", "400", "500", "600", "700"],
  subsets: ["latin"],
  display: "swap",
  variable: "--font-exo2",
});

const oracleSans = localFont({
  src: [
    { path: "../../public/fonts/OracleSans/OracleSans_Lt.ttf", weight: "300", style: "normal" },
    { path: "../../public/fonts/OracleSans/OracleSans_Rg.ttf", weight: "400", style: "normal" },
    { path: "../../public/fonts/OracleSans/OracleSans_SBd.ttf", weight: "500", style: "normal" },
    { path: "../../public/fonts/OracleSans/OracleSans_Bd.ttf", weight: "600", style: "normal" },
    { path: "../../public/fonts/OracleSans/OracleSans_XBd.ttf", weight: "700", style: "normal" },
  ],
  variable: "--font-oracle-sans",
  display: "swap",
});


export const dynamic = 'force-dynamic';

export const metadata = {
  title: "OCI Enterprise AI Agents",
  description: "Chat with our AI assistant",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" className={`${roboto.variable} ${exo2.variable} ${oracleSans.variable}`}>
      <body>
        <AppRouterCacheProvider>
          <ThemeProvider theme={theme}>{children}</ThemeProvider>
        </AppRouterCacheProvider>
      </body>
    </html>
  );
}
