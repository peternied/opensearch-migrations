'use client';

import { useState } from 'react';
import Header from '@cloudscape-design/components/header';
import Container from '@cloudscape-design/components/container';
import SpaceBetween from '@cloudscape-design/components/space-between';
import FormField from '@cloudscape-design/components/form-field';
import FileUpload from '@cloudscape-design/components/file-upload';
import Box from '@cloudscape-design/components/box';
import Alert from '@cloudscape-design/components/alert';

interface SourceConfig {
  host?: string;
  username?: string;
  awsRegion?: string;
  awsServiceSigningName?: string;
  insecure?: boolean;
}

export default function TemplateUploadViewer() {
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [sourceConfig, setSourceConfig] = useState<SourceConfig | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileUpload = (files: File[]) => {
    if (files.length > 0) {
      const file = files[0];
      setUploadedFile(file);
      parseTemplateFile(file);
    }
  };

  const parseTemplateFile = (file: File) => {
    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const json = JSON.parse(event.target?.result as string);
        // Assume the source is nested under json.source for this example
        setSourceConfig(json.source || {});
        setError(null);
      } catch (err) {
        setSourceConfig(null);
        setError(
          'Failed to parse JSON template. Please check the file format.' + err
        );
      }
    };
    reader.readAsText(file);
  };

  return (
    <SpaceBetween size="l">
      <FormField label="Upload Template JSON">
        <FileUpload
          accept=".json"
          onChange={({ detail }) => handleFileUpload(detail.value)}
          value={uploadedFile ? [uploadedFile] : []}
          i18nStrings={{
            uploadButtonText: () => 'Upload file',
            dropzoneText: () => 'Drop template JSON file here or choose one',
            removeFileAriaLabel: (e) => `Remove file ${e}`,
            errorIconAriaLabel: 'Error'
          }}
        />
      </FormField>

      {error && <Alert type="error">{error}</Alert>}

      {sourceConfig && (
        <Container
          header={<Header variant="h2">Source Details from Template</Header>}
        >
          <SpaceBetween size="s">
            <Box variant="code">Host: {sourceConfig.host || 'N/A'}</Box>
            <Box variant="code">Username: {sourceConfig.username || 'N/A'}</Box>
            <Box variant="code">
              AWS Region: {sourceConfig.awsRegion || 'N/A'}
            </Box>
            <Box variant="code">
              AWS Service Signing Name:{' '}
              {sourceConfig.awsServiceSigningName || 'N/A'}
            </Box>
            <Box variant="code">
              Insecure SSL: {sourceConfig.insecure ? 'Yes' : 'No'}
            </Box>
          </SpaceBetween>
        </Container>
      )}
    </SpaceBetween>
  );
}
