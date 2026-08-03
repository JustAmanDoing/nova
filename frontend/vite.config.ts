import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      input: {
        intake: "index.html",
        chat: "chat.html",
        focus: "focus.html",
        archive: "archive.html",
      },
    },
  },
  server: {
    host: "0.0.0.0",
    port: 5173,
  },
});
