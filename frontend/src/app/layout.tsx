import AppLayoutWrapper from '@/components/layout/cloudscape-layout';
import { MigrationSessionProvider } from '@/context/migration-session';

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html>
      <body>
        <MigrationSessionProvider>
          <AppLayoutWrapper>{children}</AppLayoutWrapper>
        </MigrationSessionProvider>
      </body>
    </html>
  );
}
