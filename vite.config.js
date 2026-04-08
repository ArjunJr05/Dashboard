import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import fs from 'fs'
import path from 'path'

// Emit client-package.json into dist/ on every build (required by Catalyst CLI)
const EmitClientPackageJson = () => ({
  name: 'emit-client-package-json',
  closeBundle() {
    const content = JSON.stringify({
      name: 'slide_web_client',
      version: '1.0.0',
      description: 'Arattai Review Dashboard Vue Client',
      homepage: 'index.html'
    }, null, '\t')
    fs.writeFileSync(
      path.resolve(__dirname, 'dist/client-package.json'),
      content + '\n'
    )
    console.log('✓ dist/client-package.json written')
  }
})

// Custom built-in HTML Reverse Proxy to seamlessly mask Cloudflare drops and bypass X-Frame Blocks natively natively
const NativeFrameProxy = () => ({
  name: 'native-frame-proxy',
  configureServer(server) {
    server.middlewares.use(async (req, res, next) => {
      if (req.url.startsWith('/raw-proxy?url=')) {
        const target = decodeURIComponent(req.url.split('?url=')[1]);
        try {
          // Native Backend HTTPS Fetch (Bypasses all Vue Frontend Browser restrictions totally natively)
          const proxyRes = await fetch(target, {
            headers: { 'User-Agent': 'WhatsApp/2', 'Accept': 'text/html' },
            redirect: 'follow'
          });
          const html = await proxyRes.text();
          
          // Inject <base> tag to securely fix any broken relative fonts, <img>, and CSS files locally natively
          const finalHtml = html.replace(/<head>/i, `<head><base href="${target}">`);
          
          res.setHeader('Content-Type', 'text/html; charset=utf-8');
          res.end(finalHtml);
        } catch (e) {
          res.statusCode = 500; 
          res.end(e.toString());
        }
        return;
      }
      next();
    })
  }
})

// https://vite.dev/config/
export default defineConfig({
  base: '/',
  server: {
    watch: {
      ignored: ['**/backend/data.json', '**/public/data.json', '**/backend/**']
    },
    allowedHosts: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5050',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
  plugins: [vue(), NativeFrameProxy(), EmitClientPackageJson()],
})
