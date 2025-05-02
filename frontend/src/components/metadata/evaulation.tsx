'use client';

import { useCallback, useEffect, useState } from 'react';
import SpaceBetween from '@cloudscape-design/components/space-between';
import StatusIndicator from '@cloudscape-design/components/status-indicator';
import Link from '@cloudscape-design/components/link';
import Button from '@cloudscape-design/components/button';
import KeyValuePairs from '@cloudscape-design/components/key-value-pairs';
import MigrationEntityTable, { MigrationEntity } from './entity-table';
import { Spinner, Box, Alert } from '@cloudscape-design/components';
import { MigrationSession } from '@/context/migration-session';

const allIndexes: MigrationEntity[] = [
  { name: 'geonames', status: 'success' },
  { name: 'nyc_taxis', status: 'success' },
  { name: 'percolator', status: 'success' },
  {
    name: 'logs-181998',
    status: 'target-failure',
    message:
      'IndexMappingTypeRemoval unsupported. Specify --multi-type-behavior.'
  },
  { name: 'logs-191998', status: 'success' },
  { name: 'logs-201998', status: 'success' },
  { name: 'logs-211998', status: 'success' }
];
const allIndexTemplates: MigrationEntity[] = [
  { name: 'daily_logs', status: 'success' }
];
const allComponentTemplates: MigrationEntity[] = [];
const allAliases: MigrationEntity[] = [{ name: 'logs-all', status: 'success' }];

export interface MetadataProps {
  session: MigrationSession;
}
export default function MetadataEvaluationAndMigration({
  session
}: MetadataProps) {
  const [mode, setMode] = useState<'evaluation' | 'migration'>('evaluation');
  const [status, setStatus] = useState<'idle' | 'running' | 'completed'>(
    'completed'
  );
  const [indexes, setIndexes] = useState<MigrationEntity[]>([]);
  const [indexTemplates, setIndexTemplates] = useState<MigrationEntity[]>([]);
  const [componentTemplates, setComponentTemplates] = useState<
    MigrationEntity[]
  >([]);
  const [aliases, setAliases] = useState<MigrationEntity[]>([]);
  const [errors, setErrors] = useState<string[]>([]);

  const validateSession = useCallback(() => {
    const validationErrors: string[] = [];
    console.log(`*** session info: ${JSON.stringify(session)}`);
    if (session?.snapshot !== 'success') {
      validationErrors.push(
        'Snapshot must be defined before running evaluation.'
      );
    }
    setErrors(validationErrors);
  }, [session, setErrors]);

  const loadItems = () => {
    setIndexes([]);
    setIndexTemplates([]);
    setComponentTemplates([]);
    setAliases([]);
    setTimeout(() => {
      setIndexes(allIndexes);
      setIndexTemplates(allIndexTemplates);
      setComponentTemplates(allComponentTemplates);
      setAliases(allAliases);
      setStatus('completed');
    }, 1500);
  };

  const runProcess = () => {
    if (errors) {
      return;
    }
    setStatus('running');
    loadItems();
  };

  const toggleMode = () => {
    setMode((prev) => (prev === 'evaluation' ? 'migration' : 'evaluation'));
    setStatus('running');
    loadItems();
  };

  useEffect(() => {
    validateSession();
  }, [validateSession]);

  const renderStatus = () => {
    if (errors.length > 0) {
      return <StatusIndicator type="stopped">Idle</StatusIndicator>;
    }

    switch (status) {
      case 'running':
        return <StatusIndicator type="in-progress">Running</StatusIndicator>;
      case 'completed':
        return <StatusIndicator type="success">Completed</StatusIndicator>;
      default:
        return <StatusIndicator type="stopped">Idle</StatusIndicator>;
    }
  };

  return (
    <SpaceBetween size="l">
      {errors.length > 0 && (
        <Box>
          {errors.map((error, idx) => (
            <Alert key={idx} statusIconAriaLabel="Error" type="error">
              {error}
            </Alert>
          ))}
        </Box>
      )}

      <KeyValuePairs
        columns={3}
        items={[
          { label: 'Status', value: renderStatus() },
          { label: 'Indices', value: indexes.length },
          { label: 'Templates', value: indexTemplates.length },
          { label: 'Aliases', value: aliases.length },
          {
            label: 'Raw Logs',
            value: (
              <Link href="#" external>
                Metadata {mode} logs
              </Link>
            )
          }
        ]}
      />

      <SpaceBetween size="s" direction="horizontal">
        <Button
          onClick={runProcess}
          disabled={status === 'running' || errors.length > 0}
        >
          Rerun {mode === 'evaluation' ? 'Evaluation' : 'Migration'}
        </Button>
        {mode === 'evaluation' && (
          <Button
            variant="primary"
            onClick={toggleMode}
            disabled={status === 'running' || errors.length > 0}
          >
            Migrate Items
          </Button>
        )}
      </SpaceBetween>

      {status === 'completed' ? (
        <>
          <MigrationEntityTable items={indexes} label="Indexes" mode={mode} />
          <MigrationEntityTable
            items={indexTemplates}
            label="Index Templates"
            mode={mode}
          />
          <MigrationEntityTable
            items={componentTemplates}
            label="Component Templates"
            mode={mode}
          />
          <MigrationEntityTable items={aliases} label="Aliases" mode={mode} />
        </>
      ) : errors.length == 0 ? (
        <>
          <Spinner /> Loading results...
        </>
      ) : (
        <></>
      )}
    </SpaceBetween>
  );
}
