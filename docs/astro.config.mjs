// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

// https://astro.build/config
export default defineConfig({
	site: 'https://algorandfoundation.github.io',
	base: '/algokit-utils-py/',
	integrations: [
		starlight({
			title: 'AlgoKit Utils Python',
			social: [
				{ icon: 'github', label: 'GitHub', href: 'https://github.com/algorandfoundation/algokit-utils-py' },
				{ icon: 'discord', label: 'Discord', href: 'https://discord.gg/algorand' },
			],
			sidebar: [
				{ label: 'Home', link: '/' },
				{
					label: 'Tutorials',
					items: [
						{ slug: 'tutorials/quick-start' },
					],
				},
				{
					label: 'Core',
					items: [
						{ slug: 'concepts/core/algorand-client' },
						{ slug: 'concepts/core/account' },
						{ slug: 'concepts/core/client' },
						{ slug: 'concepts/core/transaction' },
						{ slug: 'concepts/core/amount' },
					],
				},
				{
					label: 'Building',
					items: [
						{ slug: 'concepts/building/app-client' },
						{ slug: 'concepts/building/typed-app-clients' },
						{ slug: 'concepts/building/app' },
						{ slug: 'concepts/building/app-deploy' },
						{ slug: 'concepts/building/asset' },
						{ slug: 'concepts/building/transfer' },
						{ slug: 'concepts/building/testing' },
					],
				},
				{
					label: 'Advanced',
					items: [
						{ slug: 'concepts/advanced/transaction-composer' },
						{ slug: 'concepts/advanced/debugging' },
						{ slug: 'concepts/advanced/dispenser-client' },
					],
				},
				{
					label: 'Migration',
					items: [
						{ slug: 'migration/v3-migration-guide' },
					],
				},
			],
		}),
	],
});
