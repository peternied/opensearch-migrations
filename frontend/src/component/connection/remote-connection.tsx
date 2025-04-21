'use client';

import { useState } from 'react';
import SpaceBetween from '@cloudscape-design/components/space-between';
import FormField from '@cloudscape-design/components/form-field';
import Input from '@cloudscape-design/components/input';
import Checkbox from '@cloudscape-design/components/checkbox';
import Button from '@cloudscape-design/components/button';
import Alert from '@cloudscape-design/components/alert';

interface ConnectionSettingsProps {
  connectionType: 'source' | 'target';
}

export default function Connection({ connectionType }: ConnectionSettingsProps) {
  const [host, setHost] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [awsRegion, setAwsRegion] = useState('');
  const [awsServiceSigningName, setAwsServiceSigningName] = useState('');
  const [insecure, setInsecure] = useState(false);

  const [isVerifying, setIsVerifying] = useState(false);
  const [verificationError, setVerificationError] = useState<string | null>(null);
  const [verificationSuccess, setVerificationSuccess] = useState(false);

  const handleVerify = async () => {
    setIsVerifying(true);
    setVerificationError(null);
    setVerificationSuccess(false);

    // Simulated verification logic — replace with real API call
    await new Promise((r) => setTimeout(r, 1000));

    if (!host || !host.startsWith('http')) {
      setVerificationError('Host must be a valid URL starting with http or https.');
    } else if (host.includes('error')) {
      setVerificationError(`Could not connect to the ${connectionType}. Please check your settings.`);
    } else {
      setVerificationSuccess(true);
    }

    setIsVerifying(false);
  };

  return (
    <SpaceBetween size="m">
      {verificationError && (
        <Alert
          type="error"
          header={`${capitalize(connectionType)} connection failed`}
          onDismiss={() => setVerificationError(null)}
        >
          {verificationError}
        </Alert>
      )}

      {verificationSuccess && (
        <Alert
          type="success"
          header={`${capitalize(connectionType)} connection successful`}
          onDismiss={() => setVerificationSuccess(false)}
        >
          The {connectionType} settings are valid and connection was established.
        </Alert>
      )}

      <FormField
        label={`${capitalize(connectionType)} Host (e.g. http://localhost:9200)`}
        description={`The ${connectionType} host and port`}
      >
        <Input
          value={host}
          onChange={({ detail }) => setHost(detail.value)}
          placeholder="http://localhost:9200"
        />
      </FormField>

      <FormField
        label={`${capitalize(connectionType)} Username`}
        description="Optional. Leave blank if no authentication is required."
      >
        <Input
          value={username}
          onChange={({ detail }) => setUsername(detail.value)}
        />
      </FormField>

      <FormField
        label={`${capitalize(connectionType)} Password`}
        description="Optional. Leave blank if no authentication is required."
      >
        <Input
          type="password"
          value={password}
          onChange={({ detail }) => setPassword(detail.value)}
        />
      </FormField>

      <FormField
        label="AWS Region"
        description="Optional. Required if using SigV4 auth (e.g., us-east-1)"
      >
        <Input
          value={awsRegion}
          onChange={({ detail }) => setAwsRegion(detail.value)}
        />
      </FormField>

      <FormField
        label="AWS Service Signing Name"
        description="Optional. e.g., 'es' for OpenSearch, 'aoss' for Serverless"
      >
        <Input
          value={awsServiceSigningName}
          onChange={({ detail }) => setAwsServiceSigningName(detail.value)}
        />
      </FormField>

      <FormField label="Allow untrusted SSL certificates">
        <Checkbox
          checked={insecure}
          onChange={({ detail }) => setInsecure(detail.checked)}
        >
          Insecure SSL (allow self-signed certs)
        </Checkbox>
      </FormField>

      <Button
        variant="primary"
        loading={isVerifying}
        onClick={handleVerify}
      >
        Verify {capitalize(connectionType)} Connection
      </Button>
    </SpaceBetween>
  );
}

function capitalize(str: string) {
  return str.charAt(0).toUpperCase() + str.slice(1);
}
