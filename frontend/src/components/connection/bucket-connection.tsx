import {
  Alert,
  Button,
  FormField,
  Input,
  SpaceBetween
} from '@cloudscape-design/components';
import { useState } from 'react';

export default function BucketConnection() {
  const [s3Bucket, setS3Bucket] = useState('');
  const [snapshotName, setSnapshotName] = useState('');

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

    if (
      s3Bucket ||
      !(s3Bucket.startsWith('http') || s3Bucket.startsWith('s3'))
    ) {
      setVerificationError(
        'Host must be a valid URL starting with s3, http or https.'
      );
    } else if (s3Bucket.includes('error')) {
      setVerificationError(
        `Could not connect to the bucket. Please check your settings.`
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
          header={`Bucket connection failed`}
          onDismiss={() => setVerificationError(null)}
        >
          {verificationError}
        </Alert>
      )}

      {verificationSuccess && (
        <Alert
          type="success"
          header={`Bucket connection successful`}
          onDismiss={() => setVerificationSuccess(false)}
        >
          The settings are valid and bucket connection was established.
        </Alert>
      )}
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
      <Button variant="primary" loading={isVerifying} onClick={handleVerify}>
        Verify Bucket
      </Button>
    </SpaceBetween>
  );
}
