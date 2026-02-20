// @ts-check
import starlight from "@astrojs/starlight";
import { defineConfig } from "astro/config";
import remarkGithubAlerts from "remark-github-alerts";

// https://astro.build/config
export default defineConfig({
  site: "https://algorandfoundation.github.io",
  base: "/algokit-utils-py/",
  trailingSlash: "always",
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
      sidebar: [
        { label: "Home", link: "/" },
        {
          label: "Getting Started",
          items: [{ slug: "tutorials/quick-start" }],
        },
        {
          label: "Core Concepts",
          items: [
            { slug: "concepts/core/algorand-client" },
            { slug: "concepts/core/account" },
            { slug: "concepts/core/transaction" },
            { slug: "concepts/core/amount" },
            { slug: "concepts/core/client" },
          ],
        },
        {
          label: "Building Applications",
          items: [
            { slug: "concepts/building/app-client" },
            { slug: "concepts/building/app-deploy" },
            { slug: "concepts/building/app" },
            { slug: "concepts/building/typed-app-clients" },
            { slug: "concepts/building/asset" },
            { slug: "concepts/building/transfer" },
            { slug: "concepts/building/testing" },
          ],
        },
        {
          label: "Advanced Topics",
          collapsed: true,
          items: [
            { slug: "concepts/advanced/transaction-composer" },
            { slug: "concepts/advanced/modular-imports" },
            { slug: "concepts/advanced/debugging" },
            { slug: "concepts/advanced/indexer" },
            { slug: "concepts/advanced/dispenser-client" },
          ],
        },
        {
          label: "Migration Guides",
          collapsed: true,
          autogenerate: { directory: "migration" },
        },
        {
          label: "Examples",
          collapsed: true,
          items: [
            { label: "Overview", link: "/examples/" },
            { label: "ABI Encoding", link: "/examples/abi/" },
            { label: "Mnemonic Utilities", link: "/examples/algo25/" },
            { label: "Algod Client", link: "/examples/algod-client/" },
            { label: "Algorand Client", link: "/examples/algorand-client/" },
            { label: "Common Utilities", link: "/examples/common/" },
            { label: "Indexer Client", link: "/examples/indexer-client/" },
            { label: "KMD Client", link: "/examples/kmd-client/" },
            { label: "Transactions", link: "/examples/transact/" },
          ],
        },
        {
          label: "API Reference",
          collapsed: true,
          items: [
            { slug: "api/algokit_utils", label: "Algokit Utils Index" },
            {
              label: "accounts",
              collapsed: true,
              autogenerate: { directory: "api/algokit_utils/accounts" },
            },
            {
              label: "algo25",
              collapsed: true,
              autogenerate: { directory: "api/algokit_utils/algo25" },
            },
            {
              label: "algorand",
              collapsed: true,
              autogenerate: { directory: "api/algokit_utils/algorand" },
            },
            {
              label: "applications",
              collapsed: true,
              autogenerate: { directory: "api/algokit_utils/applications" },
            },
            {
              label: "assets",
              collapsed: true,
              autogenerate: { directory: "api/algokit_utils/assets" },
            },
            {
              label: "clients",
              collapsed: true,
              autogenerate: { directory: "api/algokit_utils/clients" },
            },
            {
              label: "config",
              collapsed: true,
              autogenerate: { directory: "api/algokit_utils/config" },
            },
            {
              label: "errors",
              collapsed: true,
              autogenerate: { directory: "api/algokit_utils/errors" },
            },
            {
              label: "models",
              collapsed: true,
              autogenerate: { directory: "api/algokit_utils/models" },
            },
            {
              label: "protocols",
              collapsed: true,
              autogenerate: { directory: "api/algokit_utils/protocols" },
            },
            {
              label: "transact",
              collapsed: true,
              autogenerate: { directory: "api/algokit_utils/transact" },
            },
            {
              label: "transactions",
              collapsed: true,
              autogenerate: { directory: "api/algokit_utils/transactions" },
            },
          ],
        },
      ],
    }),
  ],
});
