# Stage 1 — build static SPA bundle
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY . .
RUN npm run generate

# Stage 2 — serve static + proxy auth/API to Django
FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/.output/public /usr/share/nginx/html/app
ENV DJANGO_UPSTREAM=http://django:8008
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]