import path from 'node:path';

const distDir = path.join(import.meta.dir, 'dist');
const indexFile = Bun.file(path.join(distDir, 'index.html'));
const port = Number(process.env.PORT || '3000');
const backendUrl = process.env.BACKEND_URL?.trim();
const assetPathPattern = /\.[a-z0-9]+$/i;

function resolveDistPath(pathname: string) {
   const normalized = path.posix.normalize(pathname);
   const relativePath = normalized
      .replace(/^\/+/, '')
      .replace(/^(\.\.\/)+/, '');

   return path.join(distDir, relativePath || 'index.html');
}

async function serveClient(pathname: string) {
   const file = Bun.file(resolveDistPath(pathname));

   if (await file.exists()) {
      return new Response(file);
   }

   if (assetPathPattern.test(pathname)) {
      return new Response('Not found.', { status: 404 });
   }

   return new Response(indexFile);
}

async function proxyApi(request: Request, url: URL) {
   if (!backendUrl) {
      return new Response('BACKEND_URL is not configured.', { status: 500 });
   }

   const target = new URL(
      `${url.pathname}${url.search}`,
      backendUrl.endsWith('/') ? backendUrl : `${backendUrl}/`
   );
   const headers = new Headers(request.headers);

   headers.delete('host');
   headers.delete('origin');

   return fetch(target, {
      method: request.method,
      headers,
      body: request.body,
   });
}

Bun.serve({
   port,
   hostname: '0.0.0.0',
   async fetch(request) {
      const url = new URL(request.url);

      if (url.pathname.startsWith('/api')) {
         return proxyApi(request, url);
      }

      return serveClient(url.pathname);
   },
});

console.log(`Client server running on http://0.0.0.0:${port}`);
