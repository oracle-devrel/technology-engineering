import { AppRouterCacheProvider } from "@mui/material-nextjs/v15-appRouter";
import { ThemeProvider } from "@mui/material/styles";
import { Exo_2, Roboto } from "next/font/google";
import { ProjectProvider } from "./contexts/ProjectsContext";
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

export const metadata = {
  title: "OCI Generative AI Agents",
  description: "Chat with our AI assistant",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" className={`${roboto.variable} ${exo2.variable}`}>
      <body>
        <AppRouterCacheProvider>
          <ThemeProvider theme={theme}>
            <ProjectProvider>{children}</ProjectProvider>
          </ThemeProvider>
        </AppRouterCacheProvider>
      </body>
    </html>
  );
}
