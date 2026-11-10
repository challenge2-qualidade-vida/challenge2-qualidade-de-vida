import path from 'node:path';

// Ajusta os Markdown de docs/ para o site:
// - remove o primeiro "# H1" (o Starlight já mostra o título da página);
// - reescreve links relativos para .md (ex.: ../decisoes.md#secao) para a rota do site.
export default function remarkDocs({ base = '' } = {}) {
	return (tree, file) => {
		if (!file.path) return;
		const docsRoot = path.resolve(file.cwd, '../docs');
		if (path.relative(docsRoot, file.path).startsWith('..')) return;

		const h1 = tree.children.findIndex((node) => node.type === 'heading' && node.depth === 1);
		if (h1 !== -1) tree.children.splice(h1, 1);

		const fileDir = path.dirname(file.path);
		const visit = (node) => {
			if (node.type === 'link' && typeof node.url === 'string') {
				const match = node.url.match(/^([^:#?]+)\.md(#.*)?$/);
				if (match) {
					const target = path.relative(docsRoot, path.resolve(fileDir, match[1]));
					if (!target.startsWith('..')) {
						node.url = `${base}/${target.split(path.sep).join('/').toLowerCase()}/${match[2] ?? ''}`;
					}
				}
			}
			node.children?.forEach(visit);
		};
		visit(tree);
	};
}
