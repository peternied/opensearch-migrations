'use client';

import SpaceBetween from '@cloudscape-design/components/space-between';
import FormField from '@cloudscape-design/components/form-field';
import Input from '@cloudscape-design/components/input';
import Checkbox from '@cloudscape-design/components/checkbox';
import { useState } from 'react';

export default function SourceConnection() {
  const [host, setHost] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [awsRegion, setAwsRegion] = useState('');
  const [awsServiceSigningName, setAwsServiceSigningName] = useState('');
  const [insecure, setInsecure] = useState(false);

  return (
    <SpaceBetween size="m">
      <FormField
        label="Source Host (e.g. http://localhost:9200)"
        description="The source host and port"
      >
        <Input
          value={host}
          onChange={({ detail }) => setHost(detail.value)}
          placeholder="http://localhost:9200"
        />
      </FormField>

      <FormField
        label="Source Username"
        description="Optional. Leave blank if no authentication is required."
      >
        <Input
          value={username}
          onChange={({ detail }) => setUsername(detail.value)}
        />
      </FormField>

      <FormField
        label="Source Password"
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
    </SpaceBetween>
  );
}
