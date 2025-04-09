'use client';

import { useState } from 'react';
import dynamic from 'next/dynamic';

const SourceConnectionForm = dynamic(
  () => import('@/component/connection/source'),
  { ssr: false }
);

import Header from '@cloudscape-design/components/header';
import Container from '@cloudscape-design/components/container';
import SpaceBetween from '@cloudscape-design/components/space-between';
import RadioGroup from '@cloudscape-design/components/radio-group';
import FormField from '@cloudscape-design/components/form-field';
import Input from '@cloudscape-design/components/input';
import TemplateUploadViewer from '@/component/template/template-upload-viewer';

export default function SourceSelectionPage() {
  const [sourceType, setSourceType] = useState('connection');

  // S3 snapshot state
  const [s3Bucket, setS3Bucket] = useState('');
  const [snapshotName, setSnapshotName] = useState('');

  return (
    <Container>
      <SpaceBetween size="l">
        <RadioGroup
          value={sourceType}
          onChange={({ detail }) => setSourceType(detail.value)}
          items={[
            { value: 'later', label: 'Select a source later' },
            { value: 'connection', label: 'Connect to Source Cluster' },
            { value: 's3snapshot', label: 'Use S3 Snapshot Repository' },
            { value: 'jsontemplate', label: 'Load from Migration Template' }
          ]}
        />

        {/* Render based on selection */}

        {sourceType === 'later' && (
          <SpaceBetween size="m">
            <Header variant="h1">Select a source later</Header>
          </SpaceBetween>
        )}

        {sourceType === 'connection' && <SourceConnectionForm />}

        {sourceType === 's3snapshot' && (
          <SpaceBetween size="m">
            <FormField
              label="S3 Bucket URI"
              description="e.g., s3://my-snapshot-bucket/repo/"
            >
              <Input
                value={s3Bucket}
                onChange={({ detail }) => setS3Bucket(detail.value)}
              />
            </FormField>
            <FormField
              label="Snapshot Name"
              description="The specific snapshot to use"
            >
              <Input
                value={snapshotName}
                onChange={({ detail }) => setSnapshotName(detail.value)}
              />
            </FormField>
          </SpaceBetween>
        )}

        {sourceType === 'jsontemplate' && (
          <SpaceBetween size="m">
            <TemplateUploadViewer></TemplateUploadViewer>
          </SpaceBetween>
        )}
      </SpaceBetween>
    </Container>
  );
}
