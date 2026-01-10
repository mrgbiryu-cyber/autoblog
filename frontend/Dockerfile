# frontend/Dockerfile
FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

# [추가됨] 빌드 시점에 변수를 받기 위한 선언
ARG NEXT_PUBLIC_API_URL
# 받은 변수를 환경변수로 설정
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

# 이제 빌드할 때 위 IP가 들어갑니다
RUN npm run build

EXPOSE 3000
CMD ["npm", "start"]