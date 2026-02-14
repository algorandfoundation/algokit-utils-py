// @ts-check
import starlight from "@astrojs/starlight";
import { defineConfig } from "astro/config";

// https://astro.build/config
export default defineConfig({
  site: "https://algorandfoundation.github.io",
  base: "/algokit-utils-py/",
  integrations: [
    starlight({
      title: "AlgoKit Utils Python",
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
        {
          label: "Tutorials",
          items: [{ slug: "tutorials/quick-start" }],
        },
        {
          label: "Core",
          items: [
            { slug: "concepts/core/algorand-client" },
            { slug: "concepts/core/account" },
            { slug: "concepts/core/client" },
            { slug: "concepts/core/transaction" },
            { slug: "concepts/core/amount" },
          ],
        },
        {
          label: "Building",
          items: [
            { slug: "concepts/building/app-client" },
            { slug: "concepts/building/typed-app-clients" },
            { slug: "concepts/building/app" },
            { slug: "concepts/building/app-deploy" },
            { slug: "concepts/building/asset" },
            { slug: "concepts/building/transfer" },
            { slug: "concepts/building/testing" },
          ],
        },
        {
          label: "Advanced",
          items: [
            { slug: "concepts/advanced/transaction-composer" },
            { slug: "concepts/advanced/debugging" },
            { slug: "concepts/advanced/dispenser-client" },
          ],
        },
        {
          label: "Migration",
          items: [{ slug: "migration/v3-migration-guide" }],
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
