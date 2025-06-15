FROM node:18-alpine

WORKDIR /app_frontend

# Copy package.json and lock file
COPY package*.json ./

# Install dependencies
# If you use npm, change to: RUN npm install
# If you use yarn, change to: RUN yarn install
RUN npm install 

# Copy the rest of the application code
COPY . .

# Build the application
# If you use npm, change to: RUN npm run build
# If you use yarn, change to: RUN yarn build
RUN npm run build

# Serve the application using a simple HTTP server
# You might want to use a more robust server like Nginx in production
EXPOSE 5173

# Command to serve the built files. 
# Vite's preview server is not recommended for production.
# Using a simple static server. Install `serve` globally in the image or use npx.
RUN npm install -g serve
CMD ["serve", "-s", "dist", "-l", "5173"]
