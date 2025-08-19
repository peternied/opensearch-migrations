"use client";

import {
  AppLayout,
  ContentLayout,
  SideNavigation,
} from "@cloudscape-design/components";
import { useState } from "react";
import "@/lib/client-config";

const sideNav = (
  <SideNavigation
    header={{
      href: "/",
      text: "Migration Assistant",
      logo: { src: "/migrations-icon-160x160.png", alt: "" },
    }}
    items={[
      {
        type: "section-group",
        title: "Migration",
        items: [
          { type: "link", href: "/", text: "Home" },
          { type: "link", href: "/createSession", text: "Create Session" },
          { type: "link", href: "/viewSession", text: "View Session" },
          { type: "link", href: "/wizard", text: "Migration Wizard" },
        ],
      },
      { type: "divider" },
      {
        type: "section-group",
        title: "Tools",
        items: [
          {
            type: "link",
            href: "/playground",
            text: "Transformation Playground",
          },
        ],
      },
      { type: "divider" },
      {
        type: "section-group",
        title: "Help",
        items: [
          { type: "link", href: "/about", text: "About" },
          {
            type: "link",
            text: "Documentation",
            href: "https://opensearch.org/docs/latest/migration-assistant/",
            external: true,
            externalIconAriaLabel: "Opens in a new tab",
          },
          {
            type: "link",
            text: "Report an Issue",
            href: "https://github.com/opensearch-project/opensearch-migrations/issues",
            external: true,
            externalIconAriaLabel: "Opens in a new tab",
          },
          {
            type: "link",
            text: "Source Code",
            href: "https://github.com/opensearch-project/opensearch-migrations",
            external: true,
            externalIconAriaLabel: "Opens in a new tab",
          },
        ],
      },
    ]}
  ></SideNavigation>
);

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const [navigationOpen, setNavigationOpen] = useState(true);
  const toggleNavigation = () => setNavigationOpen((prev) => !prev);

  return (
    <html lang="en">
      <body>
        <AppLayout
          navigationOpen={navigationOpen}
          onNavigationChange={toggleNavigation}
          navigation={sideNav}
          toolsHide={true}
          content={
            <ContentLayout>
              <div className="contentPlaceholder">{children}</div>
            </ContentLayout>
          }
        />
      </body>
    </html>
  );
}
