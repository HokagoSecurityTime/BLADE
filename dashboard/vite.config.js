import { defineConfig } from 'vite';
export default defineConfig({server:{proxy:{'/api':{target:process.env.BLADE_ADMIN_URL || 'http://localhost:8100', rewrite:path=>path.replace(/^\/api/,'')}}}});
