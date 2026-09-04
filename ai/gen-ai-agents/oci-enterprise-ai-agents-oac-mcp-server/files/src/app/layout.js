// Copyright (c) 2026 Oracle and/or its affiliates.
// Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

import "./globals.css";

export const metadata = {
  title: "OCI Enterprise AI Agents - OAC MCP Server",
  description:
    "React assistant that queries governed Oracle Analytics Cloud data through MCP and renders charts.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
