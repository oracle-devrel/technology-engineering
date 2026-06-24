import { AppRouterCacheProvider } from "@mui/material-nextjs/v15-appRouter";
import { ThemeProvider } from "@mui/material/styles";
import localFont from "next/font/local";
import Script from "next/script";
import { ProjectProvider } from "./contexts/ProjectsContext";
import "./globals.css";
import theme from "./theme/theme";

const roboto = localFont({
  src: [
    {
      path: "../../public/fonts/roboto/Roboto-Light.ttf",
      weight: "300",
      style: "normal",
    },
    {
      path: "../../public/fonts/roboto/Roboto-Regular.ttf",
      weight: "400",
      style: "normal",
    },
    {
      path: "../../public/fonts/roboto/Roboto-Medium.ttf",
      weight: "500",
      style: "normal",
    },
    {
      path: "../../public/fonts/roboto/Roboto-Bold.ttf",
      weight: "700",
      style: "normal",
    },
  ],
  variable: "--font-roboto",
  display: "swap",
});

const exo2 = localFont({
  src: [
    {
      path: "../../public/fonts/exo2/Exo2-Light.ttf",
      weight: "300",
      style: "normal",
    },
    {
      path: "../../public/fonts/exo2/Exo2-Regular.ttf",
      weight: "400",
      style: "normal",
    },
    {
      path: "../../public/fonts/exo2/Exo2-Medium.ttf",
      weight: "500",
      style: "normal",
    },
    {
      path: "../../public/fonts/exo2/Exo2-SemiBold.ttf",
      weight: "600",
      style: "normal",
    },
    {
      path: "../../public/fonts/exo2/Exo2-Bold.ttf",
      weight: "700",
      style: "normal",
    },
  ],
  variable: "--font-exo2",
  display: "swap",
});

export const metadata = {
  title: "ODA Hub",
  description: "Chat with our AI assistant",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" className={`${roboto.variable} ${exo2.variable}`}>
      <body>
        <Script src="/web-sdk.js" strategy="beforeInteractive" />
        <AppRouterCacheProvider>
          <ThemeProvider theme={theme}>
            <ProjectProvider>{children}</ProjectProvider>
          </ThemeProvider>
        </AppRouterCacheProvider>
      </body>
    </html>
  );
}
