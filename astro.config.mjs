// @ts-check
import { defineConfig } from "astro/config";
import sitemap from "@astrojs/sitemap";

export default defineConfig({
  site: "https://iropo.org",
  trailingSlash: "ignore",
  // Keep authored whitespace so inline links inside wrapped text keep their spaces.
  compressHTML: false,
  integrations: [
    sitemap({
      filter: (page) => !page.includes("/404") && !page.includes("/contact/sent"),
    }),
  ],
  build: {
    format: "directory",
  },
  vite: {
    build: {
      // Per-state pages embed large static tables; keep warnings meaningful.
      chunkSizeWarningLimit: 1500,
    },
  },
});
