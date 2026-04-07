FROM node:20-alpine AS base

# 1. Instalar dependencias puras (separadas para cacheo rápido)
FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

# 2. Builder que crea la versión standalone
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

ENV NEXT_TELEMETRY_DISABLED=1
# Genera el /app/.next/standalone
RUN npm run build

# 3. Microvisor de final - Imagen de producción hiperligera
FROM base AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copia solo lo estrictamente necesario
COPY --from=builder /app/public ./public

# Directorios correctos para renderizado
RUN mkdir .next
RUN chown nextjs:nodejs .next

# Los archivos generados por la config "standalone"
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# El entrypoint de la versión standalone no usa 'npm run start'
CMD ["node", "server.js"]
