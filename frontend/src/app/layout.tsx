'use client';
import React, { useState } from 'react';
import {
  AppLayout,
  ContentLayout,
  SideNavigation
} from '@cloudscape-design/components';
import { I18nProvider } from '@cloudscape-design/components/i18n';
import messages from '@cloudscape-design/components/i18n/messages/all.en';

const LOCALE = 'en';

export default function AppLayoutPreview({
  children
}: {
  children: React.ReactNode;
}) {

  const [navigationOpen, setNavigationOpen] = useState(true);
  const toggleNavigation = () => {
    setNavigationOpen((prev) => !prev);
  };

  return (
    <html>
      <body>
        <I18nProvider locale={LOCALE} messages={[messages]}>
          <AppLayout
            navigationOpen={navigationOpen}
            onNavigationChange={toggleNavigation}
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
                    type: 'section-group',
                    title: 'Help',
                    items: [
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
            content={
              <ContentLayout>
                <div className="contentPlaceholder">{children}</div>
              </ContentLayout>
            }
          />
        </I18nProvider>
      </body>
    </html>
  );
}
