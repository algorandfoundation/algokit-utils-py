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
			// TODO: Sidebar entries will be added as content pages are created in subsequent commits
			sidebar: [
				{ label: 'Home', link: '/' },
			],
		}),
	],
});
