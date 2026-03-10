FROM oven/bun:1 AS deps

WORKDIR /app

COPY package.json bun.lock ./
COPY packages/client/package.json packages/client/package.json

RUN bun install --frozen-lockfile

FROM deps AS build

COPY packages/client packages/client

WORKDIR /app/packages/client

RUN bun run build

FROM oven/bun:1 AS runtime

WORKDIR /app

COPY --from=build /app/packages/client/dist ./dist
COPY packages/client/server.ts ./server.ts

EXPOSE 3000

CMD ["bun", "run", "server.ts"]
