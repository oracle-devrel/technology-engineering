# ==================================================================
# Multi-stage Dockerfile for the React/Vite frontend
#
# Stage 1 (build)  — install deps, type-check, and build with Vite
# Stage 2 (serve)  — serve the static bundle via nginx:alpine
#
# Target image size: < 50 MB (nginx:alpine ~23 MB + built assets)
# ==================================================================

# ------------------------------------------------------------------
# Stage 1: Build
# ------------------------------------------------------------------
FROM node:18-alpine AS build

WORKDIR /app

# Copy dependency manifests first for optimal Docker layer caching.
# A change to source code alone will NOT invalidate the npm install layer.
COPY package.json package-lock.json ./

# --legacy-peer-deps: required because several @react-pdf-viewer
# packages declare peer-dependency ranges that conflict with each
# other under strict resolution.
RUN npm ci --legacy-peer-deps

# Copy the rest of the source tree
COPY . .

# VITE_API_URL is intentionally left empty at build time so that
# the frontend makes requests to the *same* origin it is served
# from. Nginx then proxies /api to the backend upstream. This
# avoids baking environment-specific URLs into the image.
ENV VITE_API_URL=""

# Type-check (tsc -b) and then build the production bundle.
# Output lands in /app/build/ per vite.config.ts -> outDir: 'build'.
RUN npm run build

# ------------------------------------------------------------------
# Stage 2: Serve
# ------------------------------------------------------------------
FROM nginx:alpine AS serve

# Remove the default nginx site
RUN rm -rf /usr/share/nginx/html/*

# Copy the Vite build output from the build stage
COPY --from=build /app/build /usr/share/nginx/html

# Copy our custom nginx configuration (replaces the default)
COPY nginx.conf /etc/nginx/nginx.conf

# nginx listens on port 80
EXPOSE 80

# Run nginx in the foreground so the container stays alive
CMD ["nginx", "-g", "daemon off;"]
