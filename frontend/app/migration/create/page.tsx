'use client';
import * as React from 'react';
import Header from '@cloudscape-design/components/header';
import SpaceBetween from '@cloudscape-design/components/space-between';
import {
  Button,
  Checkbox,
  Container,
  Form,
  RadioGroup
} from '@cloudscape-design/components';
import { CheckboxWrapper } from '@cloudscape-design/components/test-utils/dom';
import Head from 'next/head';

export default function Page() {
  const [sourceChoice, setSource] = React.useState("endpoint");
  const [authType, setAuthType] = React.useState("none");

  return (
    <SpaceBetween size="m">
      <Header variant="h1">Create a migration</Header>

      <Container>
        <form onSubmit={(e) => e.preventDefault()}>
          <Form
            actions={
              <SpaceBetween direction="horizontal" size="xs">
                <Button formAction="none" variant="link">
                  Cancel
                </Button>
                <Button variant="primary">Submit</Button>
              </SpaceBetween>
            }
            header={<Header variant="h1">Select Source</Header>}
          >
            <SpaceBetween direction="vertical" size="l">
                <Container header={<Header variant="h2">Source Type</Header>}>
                <RadioGroup
                      onChange={({ detail }) => setSource(detail.value)}
                      value={sourceChoice}
                      items={[
                        {
                          value: "endpoint",
                          label: "Endpoint",
                          description: "An online source cluster that can receive requests"
                        },
                        {
                          value: "snapshot",
                          label: "Snapshot",
                          description: "A snapshot created on a source cluster."
                        },
                        {
                          value: "template",
                          label: "Template",
                          description: "Load data from an previous migration session."
                        }
                      ]}
                />
                </Container>
                <Container header={<Header variant='h2'>Endpoint Authentication</Header>}>
                <RadioGroup
                      onChange={({ detail }) => setSource(detail.value)}
                      value={sourceChoice}
                      items={[
                        {
                          value: "none",
                          label: "No Authentication",
                          description: "The cluster does not check for authentication."
                        },
                        {
                          value: "username",
                          label: "Username/Password",
                          description: "The cluster accepts username and password, also called HTTP Basic Authentication."
                        },
                        {
                          value: "sigv4",
                          label: "AWS Sigv4",
                          description: "The cluster accepts requests signed with AWS Sigv4."
                        }
                      ]}
                />
                </Container>
            </SpaceBetween>

            
          </Form>
        </form>
      </Container>
    </SpaceBetween>
  );
}
