
# Stage 1: Build the React application
FROM node:22-alpine AS build

WORKDIR /app

# Copy dependency manifests first
COPY package*.json ./

# Install exactly the dependencies in package-lock.json
RUN npm ci

# Copy React source code and Vite configuration
COPY . .

# Generate the production frontend in /app/dist
RUN npm run build

# Stage 2: Serve the built frontend using Nginx
FROM nginx:alpine

# Configure Nginx to serve React and proxy API requests
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy the compiled frontend from the build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Nginx listens on port 80 inside the container
EXPOSE 80

# Run Nginx in the foreground
CMD ["nginx", "-g", "daemon off;"]
