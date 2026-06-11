// Copyright (c) 2026 Oracle and/or its affiliates.
// SPDX-License-Identifier: UPL-1.0

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": process.env.VITE_API_PROXY_TARGET ?? "http://localhost:8000"
    }
  }
});
