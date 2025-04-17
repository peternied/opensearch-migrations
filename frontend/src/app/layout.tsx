'use client';
import React from 'react';
import {
  AppLayout,
  BreadcrumbGroup,
  ContentLayout,
  HelpPanel,
  SideNavigation
} from '@cloudscape-design/components';
import { I18nProvider } from '@cloudscape-design/components/i18n';
import messages from '@cloudscape-design/components/i18n/messages/all.en';
import { MigrationSessionProvider } from '@/context/migration-session';

const LOCALE = 'en';

export default function AppLayoutPreview({
  children
}: {
  children: React.ReactNode;
}) {
  return (
    <html>
      <body>
        <MigrationSessionProvider>
          <I18nProvider locale={LOCALE} messages={[messages]}>
            <AppLayout
              breadcrumbs={
                <BreadcrumbGroup
                  items={[
                    { text: 'Home', href: '#' },
                    { text: 'Service', href: '#' }
                  ]}
                />
              }
              navigationOpen={true}
              onNavigationChange={() => true}
              navigation={
                <SideNavigation
                  header={{
                    href: '#',
                    text: 'Migration Assistant',
                    logo: { src: 'migrations-icon-160x160.png', alt: '' }
                  }}
                  items={[
                    { type: 'link', text: `Overview`, href: `/` },
                    { type: 'divider' },
                    {
                      type: 'link',
                      text: `Select Source`,
                      href: `/step-page?step=0`
                    },
                    {
                      type: 'link',
                      text: `Traffic Capture`,
                      href: `/step-page?step=1`
                    },
                    {
                      type: 'link',
                      text: `Select Target`,
                      href: `/step-page?step=2`
                    },
                    {
                      type: 'link',
                      text: `Create Snapshot`,
                      href: `/step-page?step=3`
                    },
                    {
                      type: 'link',
                      text: `Metadata`,
                      href: `/step-page?step=4`
                    },
                    {
                      type: 'link',
                      text: `Backfill`,
                      href: `/step-page?step=5`
                    },
                    {
                      type: 'link',
                      text: `Traffic Replay`,
                      href: `/step-page?step=6`
                    },
                    {
                      type: 'link',
                      text: `Migration Review`,
                      href: `/step-page?step=7`
                    },
                    { type: 'link', text: `Tear down`, href: `/teardown` },
                    { type: 'divider' },
                    { type: 'link', text: 'About', href: '/about' },
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
              }
              tools={
                <HelpPanel header={<h2>Overview</h2>}>Help content</HelpPanel>
              }
              content={
                <ContentLayout>
                  <div className="contentPlaceholder">{children}</div>
                </ContentLayout>
              }
              // splitPanel={
              //   <SplitPanel header="Migration Status">
              //     Migration status details
              //   </SplitPanel>
              // }
            />
          </I18nProvider>
        </MigrationSessionProvider>
      </body>
    </html>
  );
}
