'use client';
import React, { useState } from 'react';
import { AppLayout, ContentLayout } from '@cloudscape-design/components';
import { I18nProvider } from '@cloudscape-design/components/i18n';
import messages from '@cloudscape-design/components/i18n/messages/all.en';
import { MigrationSessionProvider } from '@/context/migration-session';
import MigrationNavItems from '@/component/nav/side-nav';
import MAHelpPanel from '../nav/help';

const LOCALE = 'en';

export default function AppLayoutWrapper({
  children
}: {
  children: React.ReactNode;
}) {
  const [navigationOpen, setNavigationOpen] = useState(true);
  const toggleNavigation = () => setNavigationOpen((prev) => !prev);

  return (
    <MigrationSessionProvider>
      <I18nProvider locale={LOCALE} messages={[messages]}>
        <AppLayout
          navigationOpen={navigationOpen}
          onNavigationChange={toggleNavigation}
          navigation={<MigrationNavItems />}
          tools={<MAHelpPanel />}
          content={
            <ContentLayout>
              <div className="contentPlaceholder">{children}</div>
            </ContentLayout>
          }
        />
      </I18nProvider>
    </MigrationSessionProvider>
  );
}
