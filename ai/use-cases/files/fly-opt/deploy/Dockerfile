# ============================================================================
# CuOPT Frontend - Multi-stage Dockerfile for OKE Deployment
# ============================================================================

# Stage 1: Build the Vite frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /app

# Copy frontend package files
COPY app/package*.json ./

# Install dependencies
RUN npm ci --only=production=false

# Copy frontend source code
COPY app/ .

# Build the frontend
RUN npm run build

# Stage 2: Production image with Nginx + Node.js
FROM node:20-alpine AS production

# Install nginx
RUN apk add --no-cache nginx

WORKDIR /app

# Copy frontend package files for server
COPY app/package*.json ./

# Install only production dependencies for the Express server
RUN npm ci --only=production

# Copy the Express server
COPY app/server/ ./server/

# Copy built frontend from builder stage
COPY --from=frontend-builder /app/dist /usr/share/nginx/html

# Copy Nginx configuration
COPY deploy/nginx.conf /etc/nginx/nginx.conf

# Copy startup script
COPY deploy/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Expose ports
# 80 - Nginx (frontend)
# 3001 - Express API server
EXPOSE 80 3001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:80/ && \
      wget --no-verbose --tries=1 --spider http://localhost:3001/health || exit 1

# Start both nginx and node server
ENTRYPOINT ["/docker-entrypoint.sh"]
