import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { docsSchema } from '@astrojs/starlight/schema';

const docsBase = '../docs';

// Os .md de docs/ não têm frontmatter: o título vem do primeiro "# H1" do arquivo.
function titleFromH1(filePath: string, root: URL, fallback: string) {
	const source = readFileSync(fileURLToPath(new URL(filePath, root)), 'utf-8');
	return source.match(/^#\s+(.+)$/m)?.[1].trim() ?? fallback;
}

export const collections = {
	docs: defineCollection({
		loader: {
			name: 'repo-docs-loader',
			load: (context) =>
				glob({ base: docsBase, pattern: '**/[^_]*.md' }).load({
					...context,
					parseData: (props) =>
						context.parseData({
							...props,
							data: {
								title: titleFromH1(props.filePath!, context.config.root, props.id),
								...props.data,
							},
						}),
				}),
		},
		schema: docsSchema(),
	}),
};
