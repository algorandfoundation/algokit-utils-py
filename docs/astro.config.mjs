// @ts-check
import starlight from "@astrojs/starlight";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "astro/config";
import remarkGithubAlerts from "remark-github-alerts";
import starlightLinksValidator from "starlight-links-validator";
import { sidebar } from "./sidebar.config";

// https://astro.build/config
export default defineConfig({
  site: "https://algorandfoundation.github.io",
  base: "/algokit-utils-py/",
  vite: { plugins: [tailwindcss()] },
  markdown: {
    remarkPlugins: [remarkGithubAlerts],
  },
  integrations: [
    starlight({
      title: "AlgoKit Utils Python",
      tableOfContents: { minHeadingLevel: 2, maxHeadingLevel: 4 },
      customCss: [
        "./src/styles/global.css",
        "./src/styles/api-reference.css",
        "remark-github-alerts/styles/github-colors-light.css",
        "remark-github-alerts/styles/github-colors-dark-media.css",
        "remark-github-alerts/styles/github-base.css",
      ],
      social: [
        {
          icon: "github",
          label: "GitHub",
          href: "https://github.com/algorandfoundation/algokit-utils-py",
        },
        {
          icon: "discord",
          label: "Discord",
          href: "https://discord.gg/algorand",
        },
      ],
      plugins: [
        // Skip link validation during devportal builds — cross-site links
        // only resolve in the full portal, not in standalone builds.
        ...(process.env.SKIP_LINK_VALIDATION
          ? []
          : [
              starlightLinksValidator({
                errorOnInvalidHashes: false,
                errorOnLocalLinks: false,
              }),
            ]),
      ],
      sidebar: [...sidebar],
    }),
  ],
});
