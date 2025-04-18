'use client';
import React, { useState } from 'react';
import {
  AppLayout,
  ContentLayout,
  HelpPanel
} from '@cloudscape-design/components';
import { I18nProvider } from '@cloudscape-design/components/i18n';
import messages from '@cloudscape-design/components/i18n/messages/all.en';
import { MigrationSessionProvider } from '@/context/migration-session';
import MigrationNavItems from '@/component/nav/side-nav';

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
        <MigrationSessionProvider>
          <I18nProvider locale={LOCALE} messages={[messages]}>
            <AppLayout
              navigationOpen={navigationOpen}
              onNavigationChange={toggleNavigation}
              navigation={<MigrationNavItems />}
              tools={
                <HelpPanel header={<h2>Overview</h2>}>Help content</HelpPanel>
              }
              content={
                <ContentLayout>
                  <div className="contentPlaceholder">{children}</div>
                </ContentLayout>
              }
            />
          </I18nProvider>
        </MigrationSessionProvider>
      </body>
    </html>
  );
}
