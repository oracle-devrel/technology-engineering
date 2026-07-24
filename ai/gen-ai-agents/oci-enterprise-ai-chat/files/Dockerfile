FROM node:22-alpine

WORKDIR /app

# Copy pre-built standalone output (built locally with npm run build)
COPY .next/standalone ./
COPY .next/static ./.next/static
COPY public ./public

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENV PORT=8080
ENV HOSTNAME=0.0.0.0

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://127.0.0.1:8080/ready || exit 1

CMD ["/entrypoint.sh"]
