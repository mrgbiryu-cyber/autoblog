FROM node:20-alpine

WORKDIR /app

# [수정] frontend/package*.json -> package*.json (이제 같은 폴더니까요)
COPY package*.json ./
RUN npm install

# [수정] frontend/ -> .
COPY . .

RUN npm run build

EXPOSE 3000
CMD ["npm", "start"]

