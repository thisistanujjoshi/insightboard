# Build the React dashboard, then serve the static bundle with nginx.
FROM node:22-alpine AS build
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
# The browser runs on the host, so the bundle targets the host-published
# data-service port (overridable at build time).
ARG VITE_DATA_API=http://localhost:8000
RUN npm run build

FROM nginx:1.27-alpine AS runtime
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 8080
HEALTHCHECK --interval=15s --timeout=5s --retries=10 \
    CMD wget -qO- http://127.0.0.1:8080/healthz || exit 1
