// @ts-check
import starlight from "@astrojs/starlight";
import { defineConfig } from "astro/config";
import remarkGithubAlerts from "remark-github-alerts";
import { sidebar } from "./sidebar.config";

// https://astro.build/config
export default defineConfig({
  site: "https://algorandfoundation.github.io",
  base: "/algokit-utils-py/",
  markdown: {
    remarkPlugins: [remarkGithubAlerts],
  },
  integrations: [
    starlight({
      title: "AlgoKit Utils Python",
      tableOfContents: { minHeadingLevel: 2, maxHeadingLevel: 4 },
      customCss: [
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
      sidebar,
    }),
  ],
});
