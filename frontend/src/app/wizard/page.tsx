"use client";

import React, { Suspense } from "react";
import { Header, Spinner, Box, Container } from "@cloudscape-design/components";
import { useSearchParams } from "next/navigation";
import SpaceBetween from "@cloudscape-design/components/space-between";

export default function WizardPage() {
  return (
    <Suspense fallback={<Spinner size="large" />}>
      <WizardPageInner />
    </Suspense>
  );
}

function WizardPageInner() {
  const searchParams = useSearchParams();
  const sessionName = searchParams.get("sessionName");

  return (
    <SpaceBetween size="m">
      <Header variant="h1">Migration Wizard</Header>
      
      <Container>
        <SpaceBetween size="l">
          <Box variant="h2">
            Session: {sessionName || "No session specified"}
          </Box>

          <Box variant="p">
            Welcome to the Migration Wizard! This page will guide you through
            the migration process step by step.
          </Box>

          <Box variant="p">
            <strong>Coming Soon:</strong> This wizard is currently under
            development. It will provide a step-by-step interface to configure
            and execute your migration process.
          </Box>

          {sessionName && (
            <Box variant="p">
              Selected session: <strong>{sessionName}</strong>
            </Box>
          )}
        </SpaceBetween>
      </Container>
    </SpaceBetween>
  );
}
