const fs = require('fs');
const path = require('path');
const globby = require('globby');
const parser = require('@babel/parser');
const traverse = require('@babel/traverse').default;

const COMPONENTS_DIR = path.join(process.cwd(), 'src/components');
const APP_DIR = path.join(process.cwd(), 'src/app');
const ROUTE_OUTPUT = path.join(process.cwd(), 'public/sitemap.json');
const COMPONENT_OUTPUT = path.join(process.cwd(), 'public/component-map.json');

async function findTSXFiles(base) {
  return await globby([`${base}/**/*.tsx`, `!**/(layout|template).tsx`]);
}

// Step 1: Component Dependency Graph for src/components
async function buildComponentGraph() {
  const graph = {};
  const files = await findTSXFiles(COMPONENTS_DIR);

  for (const file of files) {
    const code = fs.readFileSync(file, 'utf-8');
    const ast = parser.parse(code, {
      sourceType: 'module',
      plugins: ['typescript', 'jsx']
    });

    const thisComponent = path.basename(file, '.tsx');
    graph[`MA:${thisComponent}`] = [];

    traverse(ast, {
      ImportDeclaration(p) {
        const importPath = p.node.source.value;
        if (
          importPath.includes('/src/components') ||
          importPath.startsWith('@/components')
        ) {
          for (const spec of p.node.specifiers) {
            if (
              spec.type === 'ImportSpecifier' ||
              spec.type === 'ImportDefaultSpecifier'
            ) {
              graph[`MA:${thisComponent}`].push(`MA:${spec.local.name}`);
            }
          }
        }
      }
    });
  }

  return graph;
}

// Step 2: Expand all transitive component dependencies
function expandComponent(component, graph, visited = new Set()) {
  if (visited.has(component)) return [];
  visited.add(component);
  const direct = graph[component] || [];
  const expanded = [...direct];
  for (const dep of direct) {
    expanded.push(...expandComponent(dep, graph, visited));
  }
  return [...new Set(expanded)];
}

// Step 3: Generate route → components and component → routes
async function buildSitemap(graph) {
  const files = await findTSXFiles(APP_DIR);
  const routeMap = [];
  const componentMap = {};

  for (const file of files) {
    const code = fs.readFileSync(file, 'utf-8');
    const ast = parser.parse(code, {
      sourceType: 'module',
      plugins: ['typescript', 'jsx']
    });

    const directImports = [];

    traverse(ast, {
      ImportDeclaration(p) {
        const importPath = p.node.source.value;

        for (const spec of p.node.specifiers) {
          if (
            spec.type !== 'ImportSpecifier' &&
            spec.type !== 'ImportDefaultSpecifier'
          )
            continue;

          const localName = spec.local.name;

          if (
            importPath.includes('/src/components') ||
            importPath.startsWith('@/components')
          ) {
            directImports.push(`MA:${localName}`);
          } else if (importPath.startsWith('@cloudscape-design/components')) {
            directImports.push(`CS:${localName}`);
          }
        }
      }
    });

    const allComponents = new Set(directImports);
    for (const comp of directImports) {
      if (comp.startsWith('MA:')) {
        expandComponent(comp, graph).forEach((c) => allComponents.add(c));
      }
    }

    let route =
      '/' +
      path
        .relative(APP_DIR, file)
        .replace(/page\.tsx$/, '')
        .replace(/\.tsx$/, '')
        .replace(/\\/g, '/')
        .replace(/\/index$/, '');

    if (route === '/page') route = '/';

    const components = [...allComponents].sort();
    routeMap.push({ route, components });

    for (const comp of components) {
      if (!componentMap[comp]) componentMap[comp] = [];
      componentMap[comp].push(route);
    }
  }

  // Sort componentMap values
  for (const comp in componentMap) {
    componentMap[comp] = [...new Set(componentMap[comp])].sort();
  }

  // Sort routeMap by route
  routeMap.sort((a, b) => a.route.localeCompare(b.route));

  return { routeMap, componentMap };
}

// Main
(async () => {
  const graph = await buildComponentGraph();
  const { routeMap, componentMap } = await buildSitemap(graph);

  fs.mkdirSync(path.dirname(ROUTE_OUTPUT), { recursive: true });
  fs.writeFileSync(ROUTE_OUTPUT, JSON.stringify(routeMap, null, 2));
  fs.writeFileSync(COMPONENT_OUTPUT, JSON.stringify(componentMap, null, 2));

  console.log(
    '✅ Tagged sitemap.json and component-map.json written with transitive + cloudscape tracking'
  );
})();
