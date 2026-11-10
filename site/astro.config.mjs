// @ts-check
import { readdirSync } from 'node:fs';
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import { unified } from '@astrojs/markdown-remark';
import remarkDocs from './src/plugins/remark-docs.mjs';

const repo = 'https://github.com/dida0982/challenge2-qualidade-de-vida';
const base = '/challenge2-qualidade-de-vida';
const docsDir = new URL('../docs/', import.meta.url);

// Sidebar gerada a partir de docs/: arquivos da raiz em "Geral" e um grupo por semana com conteúdo.
const hasMarkdown = (dir) => readdirSync(new URL(`${dir}/`, docsDir)).some((f) => f.endsWith('.md'));
const semanas = readdirSync(docsDir, { withFileTypes: true })
	.filter((d) => d.isDirectory() && /^semana-\d+$/.test(d.name) && hasMarkdown(d.name))
	.map((d) => d.name)
	.sort((a, b) => Number(a.split('-')[1]) - Number(b.split('-')[1]));
const geral = readdirSync(docsDir)
	.filter((f) => f.endsWith('.md'))
	.map((f) => f.replace(/\.md$/, '').toLowerCase());

export default defineConfig({
	site: 'https://dida0982.github.io',
	base,
	markdown: {
		processor: unified({ remarkPlugins: [[remarkDocs, { base }]] }),
	},
	integrations: [
		starlight({
			title: 'EconoMIA',
			description: 'Challenge 2 — Qualidade de Vida · Residência em IA Brasília',
			favicon: '/favicon.svg',
			locales: { root: { label: 'Português', lang: 'pt-BR' } },
			social: [{ icon: 'github', label: 'GitHub', href: repo }],
			customCss: ['./src/styles/paleta.css'],
			sidebar: [
				{ label: 'Geral', items: geral },
				...semanas.map((s) => ({
					label: `Semana ${s.split('-')[1]}`,
					items: [{ autogenerate: { directory: s } }],
				})),
			],
		}),
	],
});
