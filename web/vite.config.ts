import { defineConfig, loadEnv, ViteDevServer } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");

  return {
    plugins: [react(), tailwindcss()],
    build: {
      outDir: "dist/static",
      emptyOutDir: true,
    },
    server: {
      allowedHosts: ["localhost"],
      proxy: {
        "/trpc": {
          target: env.VITE_BACKEND_URL,
          prependPath: false,
        },
      },
      watch: {
        ignored: ["**/*.db"],
        usePolling: true,
      },
    },
  };
});
