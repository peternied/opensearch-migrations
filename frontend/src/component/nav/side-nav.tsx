import { useMigrationSessions } from '@/context/migration-session';
import {
  SideNavigation,
  SideNavigationProps
} from '@cloudscape-design/components';

export default function MigrationNavItems() {
  const { sessions } = useMigrationSessions();
  const sessionNavLinks: SideNavigationProps.Link[] = sessions.map(
    (session) => {
      return {
        type: 'link',
        text: session.name,
        href: `/session?id=${session.id}`
      };
    }
  );

  return (
    <SideNavigation
      header={{
        href: '#',
        text: 'Migration Assistant',
        logo: { src: 'migrations-icon-160x160.png', alt: '' }
      }}
      items={[
        { type: 'link', text: `Overview`, href: `/` },
        { type: 'link', text: 'About', href: '/about' },
        { type: 'link', text: `Tear down`, href: `/teardown` },
        { type: 'divider' },
        {
          type: 'section-group',
          title: 'Migration Sessions',
          items: sessionNavLinks
        },
        { type: 'divider' },
        {
          type: 'section-group',
          title: 'Help',
          items: [
            {
              type: 'link',
              text: 'Documentation',
              href: 'https://opensearch.org/docs/latest/migration-assistant/',
              external: true,
              externalIconAriaLabel: 'Opens in a new tab'
            },
            {
              type: 'link',
              text: 'Report an Issue',
              href: 'https://github.com/opensearch-project/opensearch-migrations/issues',
              external: true,
              externalIconAriaLabel: 'Opens in a new tab'
            },
            {
              type: 'link',
              text: 'Source Code',
              href: 'https://github.com/opensearch-project/',
              external: true,
              externalIconAriaLabel: 'Opens in a new tab'
            }
          ]
        }
      ]}
    />
  );
}
