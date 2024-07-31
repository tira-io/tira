// Plugins
import vue from '@vitejs/plugin-vue'
import vuetify, { transformAssetUrls } from 'vite-plugin-vuetify'

// Utilities
import { defineConfig } from 'vite'
import { fileURLToPath, URL } from 'node:url'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    vue({ template: { transformAssetUrls } }),
    // https://github.com/vuetifyjs/vuetify-loader/tree/next/packages/vite-plugin
    vuetify({ autoImport: true }),
  ],
  define: { 'process.env': {} },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
    extensions: ['.js', '.json', '.jsx', '.mjs', '.ts', '.tsx', '.vue'],
  },
  server: {
    port: 3000,
    strictPort: true,
  },
  build: {
    rollupOptions: {
      output: {
        // TODO: We would usually like to use assets/ here, but we first have to fix this disraptor problem: https://github.com/disraptor/disraptor/issues/33
        // TODO: Documentation
        assetFileNames: 'tira-frontend/assets-public/[name].[ext]',
        chunkFileNames: 'tira-frontend/chunks/[name].js',
        entryFileNames: 'tira-frontend/entries/[name].js',
      },
    },
    outDir: 'static/',
  },
  experimental: {
    renderBuiltUrl(filename: string, { hostType }: { hostType: 'js' | 'css' | 'html' }) {
      // TIRA expects resourecs/assets at this location
      return '/' + filename
    }
  }
})
