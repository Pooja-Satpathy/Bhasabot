# syntax=docker/dockerfile:1

# ── Stage 1: Build React Application ─────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

# Copy dependency manifests
COPY package.json package-lock.json ./

# Install dependencies cleanly
RUN npm ci --silent || npm install --silent

# Copy frontend source code
COPY . .

# Build for production
ENV NODE_ENV=production

RUN npm run build

# ── Stage 2: Production Nginx Server ────────────────────────────────────────
FROM nginx:1.27-alpine-slim AS runner

# Remove default Nginx site files
RUN rm -rf /usr/share/nginx/html/* /etc/nginx/conf.d/default.conf

# Copy custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy compiled assets from the builder stage
COPY --from=builder /app/build /usr/share/nginx/html

# Expose HTTP port
EXPOSE 80

# Health check
HEALTHCHECK --interval=20s --timeout=5s --start-period=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
