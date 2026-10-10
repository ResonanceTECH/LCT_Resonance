FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
# The real backend serves the frontend contract under /api (nginx proxies it).
# VITE_USE_MOCKS=true builds the offline MSW demo instead.
ARG VITE_USE_MOCKS=false
ARG VITE_API_BASE_URL=/api
ENV VITE_USE_MOCKS=$VITE_USE_MOCKS \
    VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
