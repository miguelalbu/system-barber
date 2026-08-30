# Multi-stage: `dev` runs the Vite dev server with HMR, `prod` serves the built
# static files from nginx. Compose uses `target: dev`; see the README to build
# the production image.

# --------------------------------------------------------------------------- #
FROM node:22-alpine AS deps

WORKDIR /app

# Only the manifests, so `npm ci` is cached until a dependency actually changes.
COPY package.json package-lock.json ./
RUN npm ci


# --------------------------------------------------------------------------- #
FROM node:22-alpine AS dev

WORKDIR /app
ENV NODE_ENV=development

COPY --from=deps /app/node_modules ./node_modules
COPY . .

EXPOSE 5173

# --host 0.0.0.0 is required: bound to localhost, the server would only answer
# inside the container.
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]


# --------------------------------------------------------------------------- #
FROM node:22-alpine AS build

WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build


# --------------------------------------------------------------------------- #
FROM nginx:1.27-alpine AS prod

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

# 127.0.0.1, not localhost: the image entrypoint only injects `listen [::]:80`
# into the stock config, so with a custom one nginx is IPv4-only — and inside
# the container `localhost` resolves to ::1 first, which would fail.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -qO- http://127.0.0.1/ >/dev/null || exit 1
