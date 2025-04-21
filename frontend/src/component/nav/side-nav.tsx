import { Link, SideNavigation } from '@cloudscape-design/components';
import DemoWrapper from '../demoWrapper';

export default function MigrationNavItems() {
  return (
    <SideNavigation
      header={{
        href: '/',
        text: 'Migration Assistant',
        logo: { src: 'migrations-icon-160x160.png', alt: '' }
      }}
      items={[
        { type: 'link', text: `Dashboard`, href: `/dashboard` },
        { type: 'link', text: 'About', href: '/about' },
        { type: 'link', text: `Tear down`, href: `/teardown` },
        {
          type: 'link',
          text: ``,
          href: '',
          info: (
            <DemoWrapper>
              <Link href="/loading">Loading page</Link>
            </DemoWrapper>
          )
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
