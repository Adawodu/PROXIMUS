# Web dashboard — build with Vite, serve the static bundle with nginx.
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
# Build-time config baked into the static bundle. VITE_API_KEY lets the dashboard
# authenticate to a key-protected API; leave empty for an unauthenticated backend.
ARG VITE_API_KEY=""
ARG VITE_API_BASE_URL=""
ENV VITE_API_KEY=$VITE_API_KEY
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
