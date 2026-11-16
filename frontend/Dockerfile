# Stage 1 — build static SPA bundle
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund

# NUXT_PUBLIC_* is inlined at `nuxt generate` time, so the key must be present
# during the build (frontend/.env is gitignored and absent in CI checkouts).
ARG NUXT_PUBLIC_GOOGLE_MAPS_API_KEY=""
ARG NUXT_PUBLIC_MAP_CENTER=""
ARG NUXT_PUBLIC_MAP_ZOOM=""
ARG NUXT_PUBLIC_MAP_REFRESH_INTERVAL=""
ENV NUXT_PUBLIC_GOOGLE_MAPS_API_KEY=$NUXT_PUBLIC_GOOGLE_MAPS_API_KEY \
    NUXT_PUBLIC_MAP_CENTER=$NUXT_PUBLIC_MAP_CENTER \
    NUXT_PUBLIC_MAP_ZOOM=$NUXT_PUBLIC_MAP_ZOOM \
    NUXT_PUBLIC_MAP_REFRESH_INTERVAL=$NUXT_PUBLIC_MAP_REFRESH_INTERVAL
COPY . .
RUN npm run generate

# Stage 2 — serve static + proxy auth/API to Django
FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/.output/public /usr/share/nginx/html
COPY entrypoint-frontend.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh
ENV DJANGO_UPSTREAM=http://django:8008
EXPOSE 80
ENTRYPOINT ["/docker-entrypoint.sh"]
