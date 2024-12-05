'use client';
import React from 'react';
import {
  AppLayout,
  BreadcrumbGroup,
  Container,
  ContentLayout,
  Flashbar,
  Header,
  HelpPanel,
  Link,
  SideNavigation,
  SplitPanel
} from '@cloudscape-design/components';
import { I18nProvider } from '@cloudscape-design/components/i18n';
import messages from '@cloudscape-design/components/i18n/messages/all.en';

const LOCALE = 'en';

export default function AppLayoutPreview({
  children
}: {
  children: React.ReactNode;
}) {
  return (
    <html>
      <body>
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
                  text: 'Service name'
                }}
                items={[
                  { type: 'link', text: `Home`, href: `/` },
                  { type: 'link', text: `Migrations`, href: `/migration` },
                  {
                    type: 'link',
                    text: `Create Migration`,
                    href: `/migration/create`
                  },
                  { type: 'link', text: `Tear down`, href: `/teardown` }
                ]}
              />
            }
            notifications={
              <Flashbar
                items={[
                  {
                    type: 'info',
                    dismissible: true,
                    onDismiss: () => true,
                    content: 'This is an info flash message.',
                    id: 'message_1'
                  }
                ]}
              />
            }
            toolsOpen={true}
            onToolsChange={() => true}
            tools={
              <HelpPanel header={<h2>Overview</h2>}>Help content</HelpPanel>
            }
            content={
              <ContentLayout
                header={
                  <Header variant="h1" info={<Link variant="info">Info</Link>}>
                    Page header
                  </Header>
                }
              >
                <Container
                  header={
                    <Header variant="h2" description="Container description">
                      Container header
                    </Header>
                  }
                >
                  <div className="contentPlaceholder">{children}</div>
                </Container>
              </ContentLayout>
            }
            splitPanel={
              <SplitPanel header="Split panel header">
                Split panel content
              </SplitPanel>
            }
          />
        </I18nProvider>
      </body>
    </html>
  );
}
