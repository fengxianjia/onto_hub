# Step 1: Build Stage
FROM node:18-alpine as build-stage

WORKDIR /app

# Copy package.json and package-lock.json (if exists)
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy frontend code and build
COPY . .
RUN npm run build

# Step 2: Production Stage
FROM nginx:stable-alpine as production-stage

# Copy built files from build stage
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Copy custom Nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
