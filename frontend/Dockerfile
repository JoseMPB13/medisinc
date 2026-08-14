# ==========================================
# ETAPA 1: Construcción (Build) con Node 18
# ==========================================
FROM node:18-alpine AS builder

WORKDIR /app

# Copiar archivos de definición de paquetes
COPY package.json package-lock.json* ./

# Instalar dependencias
RUN npm ci || npm install

# Copiar el resto del código del frontend
COPY . .

# Compilar la aplicación para producción
RUN npm run build

# ==========================================
# ETAPA 2: Servidor Web Nginx de Producción
# ==========================================
FROM nginx:alpine

# Copiar configuración personalizada de Nginx para SPA
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copiar los archivos estáticos compilados desde la etapa anterior
COPY --from=builder /app/dist /usr/share/nginx/html

# Exponer el puerto 80
EXPOSE 80

# Iniciar Nginx en primer plano
CMD ["nginx", "-g", "daemon off;"]
