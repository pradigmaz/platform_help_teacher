import { access, lstat, mkdir, rm, symlink } from 'node:fs/promises';
import http from 'node:http';
import https from 'node:https';
import path from 'node:path';
import { spawn } from 'node:child_process';
import { URL } from 'node:url';

const projectRoot = process.cwd();
const standaloneRoot = path.join(projectRoot, '.next', 'standalone');
const standaloneNextRoot = path.join(standaloneRoot, '.next');
const localProxyHost = process.env.SMOKE_PROXY_HOST ?? '127.0.0.1';
const localProxyPort = Number.parseInt(process.env.SMOKE_PROXY_PORT ?? '8000', 10);

function createBackendProxy() {
  const backendUrl = new URL(process.env.BACKEND_URL ?? 'http://127.0.0.1');
  const upstreamModule = backendUrl.protocol === 'https:' ? https : http;

  const server = http.createServer((request, response) => {
    const upstreamRequest = upstreamModule.request(
      {
        protocol: backendUrl.protocol,
        hostname: backendUrl.hostname,
        port: backendUrl.port || (backendUrl.protocol === 'https:' ? 443 : 80),
        method: request.method,
        path: request.url,
        headers: {
          ...request.headers,
          host: backendUrl.host,
        },
      },
      (upstreamResponse) => {
        response.writeHead(upstreamResponse.statusCode ?? 502, upstreamResponse.headers);
        upstreamResponse.pipe(response);
      },
    );

    upstreamRequest.on('error', (error) => {
      response.writeHead(502, { 'content-type': 'text/plain; charset=utf-8' });
      response.end(`Smoke proxy error: ${error.message}`);
    });

    request.pipe(upstreamRequest);
  });

  return {
    server,
    async listen() {
      await new Promise((resolve, reject) => {
        server.once('error', reject);
        server.listen(localProxyPort, localProxyHost, () => {
          server.off('error', reject);
          resolve(undefined);
        });
      });
    },
    async close() {
      await new Promise((resolve) => {
        server.close(() => resolve(undefined));
      });
    },
  };
}

async function exists(targetPath) {
  try {
    await access(targetPath);
    return true;
  } catch {
    return false;
  }
}

async function ensureLinked(sourcePath, targetPath) {
  if (!(await exists(sourcePath))) {
    return;
  }

  await mkdir(path.dirname(targetPath), { recursive: true });

  if (await exists(targetPath)) {
    const stats = await lstat(targetPath);
    if (stats.isSymbolicLink()) {
      return;
    }

    await rm(targetPath, { recursive: true, force: true });
  }

  const relativeSource = path.relative(path.dirname(targetPath), sourcePath);
  await symlink(relativeSource, targetPath, 'dir');
}

async function main() {
  await ensureLinked(path.join(projectRoot, 'public'), path.join(standaloneRoot, 'public'));
  await ensureLinked(path.join(projectRoot, '.next', 'static'), path.join(standaloneNextRoot, 'static'));
  const backendProxy = createBackendProxy();
  await backendProxy.listen();

  const child = spawn(process.execPath, [path.join(standaloneRoot, 'server.js')], {
    cwd: projectRoot,
    env: {
      ...process.env,
      HOSTNAME: process.env.HOSTNAME ?? '127.0.0.1',
      PORT: process.env.PORT ?? process.env.PLAYWRIGHT_TEST_PORT ?? '3100',
    },
    stdio: 'inherit',
  });

  child.on('exit', async (code, signal) => {
    await backendProxy.close();
    if (signal) {
      process.kill(process.pid, signal);
      return;
    }

    process.exit(code ?? 0);
  });
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
