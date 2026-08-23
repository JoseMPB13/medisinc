# =============================================================================
# DOCKERFILE FRONTEND - MEDISINC-IA (Multi-Stage Build React + Vite + Nginx)
# =============================================================================

# ETAPA 1: Compilación de la aplicación con Node.js
FROM node:20-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN npm ci || npm install

COPY . .
RUN npm run build

# ETAPA 2: Servidor Nginx ultra-ligero para producción
FROM nginx:alpine

# Copiar bundle compilado de React
COPY --from=build /app/dist /usr/share/nginx/html

# Copiar configuración de Nginx con soporte para React Router
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
