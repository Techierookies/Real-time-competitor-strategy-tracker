# The API base URL is baked in at build time, because Vite inlines
# import.meta.env into the bundle. Pass it as a build argument.

FROM node:20-alpine AS builder

ARG VITE_API_BASE_URL=http://localhost:8000
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build


FROM nginx:1.27-alpine AS runtime

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
