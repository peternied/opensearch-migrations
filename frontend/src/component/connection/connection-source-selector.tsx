'use client';

import { useState } from 'react';
import SpaceBetween from '@cloudscape-design/components/space-between';
import RadioGroup from '@cloudscape-design/components/radio-group';
import TemplateUploadViewer from '@/component/template/template-upload-viewer';
import { Box } from '@cloudscape-design/components';
import SourceConnectionForm from './remote-connection';
import BucketConnection from './bucket-connection';

export default function SourceSelectionPage() {
  const [sourceType, setSourceType] = useState('connection');

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
          { value: 'template', label: 'Load from Migration Template' }
        ]}
      />

      {sourceType === 'connection' && (
        <SourceConnectionForm connectionType="source" />
      )}

      {sourceType === 's3snapshot' && <BucketConnection />}

      {sourceType === 'template' && (
        <SpaceBetween size="m">
          <TemplateUploadViewer></TemplateUploadViewer>
        </SpaceBetween>
      )}
    </SpaceBetween>
  );
}
