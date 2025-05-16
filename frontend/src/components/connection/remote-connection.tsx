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

export default function Connection({
  connectionType
}: ConnectionSettingsProps) {
  const [host, setHost] = useState(`http://${connectionType}.cluster.local:9200`);
  const [username, setUsername] = useState(connectionType == 'source' ? 'admin' : '');
  const [password, setPassword] = useState(connectionType == 'source' ? 'arn:aws:secretsmanager:us-east-1:123456789012:secret:my-plaintext-secret-AbC123' : '');
  const [awsRegion, setAwsRegion] = useState(connectionType == 'source' ? '' : 'us-east-2');
  const [awsServiceSigningName, setAwsServiceSigningName] = useState(connectionType == 'source' ? '' : 'es');
  const [insecure, setInsecure] = useState(connectionType == 'source' ? true : false);

  const [isVerifying, setIsVerifying] = useState(false);
  const [verificationError, setVerificationError] = useState<string | null>(
    null
  );
  const [verificationSuccess, setVerificationSuccess] = useState(false);

  const handleVerify = async () => {
    setIsVerifying(true);
    setVerificationError(null);
    setVerificationSuccess(false);

    // Simulated verification logic — replace with real API call
    await new Promise((r) => setTimeout(r, 1000));

    if (!host || !host.startsWith('http')) {
      setVerificationError(
        'Host must be a valid URL starting with http or https.'
      );
    } else if (host.includes('error')) {
      setVerificationError(
        `Could not connect to the ${connectionType}. Please check your settings.`
      );
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
          The {connectionType} settings are valid and connection was
          established.
        </Alert>
      )}

      <FormField
        label={`${capitalize(connectionType)} Host (e.g. http://localhost:9200)`}
        description={`The ${connectionType} host and port`}
      >
        <Input
          value={host}
          readOnly
          onChange={({ detail }) => setHost(detail.value)}
        />
      </FormField>

      {!!username &&
      <FormField
        label={`${capitalize(connectionType)} Username`}
        description="Optional. Leave blank if no authentication is required."
      >
        <Input
          value={username}
          readOnly
          onChange={({ detail }) => setUsername(detail.value)}
        />
      </FormField>}

      {!!password && 
      <FormField
        label={`${capitalize(connectionType)} Password Arn`}
        description="Leave blank if no authentication is required."
      >
        <Input
        readOnly
          value={password}
          onChange={({ detail }) => setPassword(detail.value)}
        />
      </FormField>}

      {!!awsRegion && 
      <FormField
        label="AWS Region"
        description="Optional. Required if using SigV4 auth (e.g., us-east-1)"
      >
        <Input
          value={awsRegion}
          readOnly
          onChange={({ detail }) => setAwsRegion(detail.value)}
        />
      </FormField>}

      { !!awsServiceSigningName &&
      <FormField
        label="AWS Service Signing Name"
        description="Optional. e.g., 'es' for OpenSearch, 'aoss' for Serverless"
      >
        <Input
          value={awsServiceSigningName}
          readOnly
          onChange={({ detail }) => setAwsServiceSigningName(detail.value)}
        />
      </FormField>}

      {insecure && <FormField label="Allow untrusted SSL certificates">
        <Checkbox
          checked={insecure}
          onChange={({ detail }) => setInsecure(detail.checked)}
          readOnly
        >
          Insecure SSL (allow self-signed certs)
        </Checkbox>
      </FormField>}

      {/* <Button variant="primary" loading={isVerifying} onClick={handleVerify}>
        Verify {capitalize(connectionType)} Connection
      </Button> */}
    </SpaceBetween>
  );
}

function capitalize(str: string) {
  return str.charAt(0).toUpperCase() + str.slice(1);
}
