# BUILD STAGE
FROM node:20 as build
ARG IS_PRODUCTION=true

WORKDIR /app

COPY ./package.json /app
COPY ./package-lock.json /app
RUN npm install --save-prod

COPY ./tsconfig.* /app
COPY ./angular.json /app
COPY . /app
RUN if [ "$IS_PRODUCTION" = "true" ]; then npm run build:prod; else npm run build:dev; fi

COPY ./public /app/dist/browser/public

# DEPLOY STAGE
FROM nginx:alpine
ARG SUBDIR=chat

COPY --from=build /app/dist/browser /usr/share/nginx/html/${SUBDIR}/

EXPOSE 80
