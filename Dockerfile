FROM node:22-alpine
WORKDIR /app
COPY client/package*.json ./client/
COPY server/package*.json ./server/
RUN cd client && npm install && cd ../server && npm install --omit=dev
COPY client ./client
COPY server ./server
RUN cd client && npm run build
ENV NODE_ENV=production
EXPOSE 3001
CMD ["node","server/index.js"]
