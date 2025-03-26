'use client';

import { useState } from 'react';
import Header from '@cloudscape-design/components/header';
import Container from '@cloudscape-design/components/container';
import SpaceBetween from '@cloudscape-design/components/space-between';
import RadioGroup from '@cloudscape-design/components/radio-group';
import FormField from '@cloudscape-design/components/form-field';
import Input from '@cloudscape-design/components/input';
import Select from '@cloudscape-design/components/select';
import Button from '@cloudscape-design/components/button';
import SourceConnectionForm from '@/component/connection/source';
import TemplateUploadViewer from '@/component/template/template-upload-viewer';

export default function SourceSelectionPage() {
  const [sourceType, setSourceType] = useState('connection');

  // S3 snapshot state
  const [s3Bucket, setS3Bucket] = useState('');
  const [snapshotName, setSnapshotName] = useState('');

  const handleContinue = () => {
  };

  return (
    <SpaceBetween size="m">
      <Header variant="h1">Select Source for Migration</Header>

      <Container>
        <SpaceBetween size="l">
          <RadioGroup
            value={sourceType}
            onChange={({ detail }) => setSourceType(detail.value)}
            items={[
              { value: 'connection', label: 'Connect to Source Cluster' },
              { value: 's3snapshot', label: 'Use S3 Snapshot Repository' },
              { value: 'jsontemplate', label: 'Load from Migration Template' },
            ]}
          />

          {/* Render based on selection */}
          {sourceType === 'connection' && <SourceConnectionForm />}

          {sourceType === 's3snapshot' && (
            <SpaceBetween size="m">
              <FormField label="S3 Bucket URI" description="e.g., s3://my-snapshot-bucket/repo/">
                <Input value={s3Bucket} onChange={({ detail }) => setS3Bucket(detail.value)} />
              </FormField>
              <FormField label="Snapshot Name" description="The specific snapshot to use">
                <Input value={snapshotName} onChange={({ detail }) => setSnapshotName(detail.value)} />
              </FormField>
            </SpaceBetween>
          )}

          {sourceType === 'jsontemplate' && (
            <SpaceBetween size="m">
              <TemplateUploadViewer>

              </TemplateUploadViewer>
            </SpaceBetween>
          )}

          <Button variant="primary" onClick={handleContinue}>Continue</Button>
        </SpaceBetween>
      </Container>
    </SpaceBetween>
  );
}
