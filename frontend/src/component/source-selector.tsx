'use client';

import { useState } from 'react';
import dynamic from 'next/dynamic';

const SourceConnectionForm = dynamic(
  () => import('@/component/connection/source'),
  { ssr: false }
);

import Header from '@cloudscape-design/components/header';
import SpaceBetween from '@cloudscape-design/components/space-between';
import RadioGroup from '@cloudscape-design/components/radio-group';
import FormField from '@cloudscape-design/components/form-field';
import Input from '@cloudscape-design/components/input';
import TemplateUploadViewer from '@/component/template/template-upload-viewer';
import { Box } from '@cloudscape-design/components';

export default function SourceSelectionPage() {
  const [sourceType, setSourceType] = useState('connection');

  // S3 snapshot state
  const [s3Bucket, setS3Bucket] = useState('');
  const [snapshotName, setSnapshotName] = useState('');

  return (
    <SpaceBetween size="l">
      <Box>
        Migration Assistant needs details to help determine the complexity of
        the migration, please select the source so these can be reviews through
        this workflow.
      </Box>
      <RadioGroup
        value={sourceType}
        onChange={({ detail }) => setSourceType(detail.value)}
        items={[
          { value: 'connection', label: 'Connect to Source Cluster' },
          { value: 's3snapshot', label: 'Use S3 Snapshot Repository' },
          { value: 'jsontemplate', label: 'Load from Migration Template' },
          { value: 'later', label: 'Select a source later' }
        ]}
      />

      {/* Render based on selection */}

      {sourceType === 'later' && (
        <SpaceBetween size="m">
          <Header variant="h3">Select a source later</Header>
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
  );
}
