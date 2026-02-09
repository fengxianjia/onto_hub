# Step 1: Build Stage
FROM node:20-alpine as build-stage

WORKDIR /app

# Copy all files first
COPY . .

# Defensive cleanup: remove any host-side node_modules and dist before installing dependencies in container
RUN rm -rf node_modules dist

# Install dependencies (on top of fresh container state)
RUN npm install

# Build the application
RUN npm run build

# Step 2: Production Stage
FROM nginx:stable-alpine as production-stage

# Copy built files from build stage
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Copy custom Nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
