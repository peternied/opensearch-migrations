'use client';

import { useEffect, useState } from 'react';
import Container from '@cloudscape-design/components/container';
import Header from '@cloudscape-design/components/header';
import SpaceBetween from '@cloudscape-design/components/space-between';
import ExpandableSection from '@cloudscape-design/components/expandable-section';
import Box from '@cloudscape-design/components/box';
import Link from '@cloudscape-design/components/link';

type RouteMapEntry = {
  route: string;
  components: string[];
};

type ComponentMap = {
  [component: string]: string[];
};

export default function UXInspectorPage() {
  const [routeMap, setRouteMap] = useState<RouteMapEntry[]>([]);
  const [componentMap, setComponentMap] = useState<ComponentMap>({});

  useEffect(() => {
    async function loadData() {
      const [routeRes, compRes] = await Promise.all([
        fetch('/sitemap.json'),
        fetch('/component-map.json'),
      ]);

      setRouteMap(await routeRes.json());
      setComponentMap(await compRes.json());
    }

    loadData();
  }, []);

  return (
    <Container header={<Header variant="h1">UX Inspector</Header>}>
      <SpaceBetween size="l">
        <ExpandableSection headerText="By Route" defaultExpanded>
          <SpaceBetween size="s">
            {routeMap.toSorted().map(({ route, components }) => (
              <Box key={route}>
                <strong>
                  <Link href={route} external={false}>
                    {route}
                  </Link>
                </strong>
                <ul>
                  {components.map((c) => (
                    <li key={c}>{c}</li>
                  ))}
                </ul>
              </Box>
            ))}
          </SpaceBetween>
        </ExpandableSection>

        <ExpandableSection headerText="By Component" defaultExpanded>
          <SpaceBetween size="s">
            {Object.entries(componentMap).toSorted().map(([component, routes]) => (
              <Box key={component}>
                <strong>{component}</strong>
                <ul>
                  {routes.map((r) => (
                    <li key={r}>
                      <Link href={r} external={false}>
                        {r}
                      </Link>
                    </li>
                  ))}
                </ul>
              </Box>
            ))}
          </SpaceBetween>
        </ExpandableSection>
      </SpaceBetween>
    </Container>
  );
}
