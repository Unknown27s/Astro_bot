FROM node:20-alpine as builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --prefer-offline --no-audit
COPY public/ ./public/
COPY src/ ./src/
COPY vite.config.js index.html ./
RUN npm run build
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
RUN cat > /etc/nginx/conf.d/default.conf << 'EOF'
server {
    listen 3000;
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }
    location /api {
        proxy_pass $API_URL;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD wget --quiet --tries=1 --spider http://localhost:3000 || exit 1
ENV API_URL=http://astrobot-backend:8080
CMD ["nginx", "-g", "daemon off;"]