FROM node:22-bookworm-slim AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM node:22-bookworm-slim AS runner

ENV NODE_ENV=production \
    APP_DIR=/app

WORKDIR /app

COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
COPY --from=builder /app/scripts/start_container.sh ./scripts/start_container.sh

RUN chmod +x ./scripts/start_container.sh

EXPOSE 3000

ENTRYPOINT ["./scripts/start_container.sh"]
