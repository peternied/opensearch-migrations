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

const allItems: MigrationEntity[] = [
  { name: 'geonames', status: 'success', type: 'Index' },
  { name: 'nyc_taxis', status: 'success', type: 'Index' },
  { name: 'percolator', status: 'success', type: 'Index' },
  {
    name: 'logs-181998',
    status: 'target-failure',
    message:
      `Create object failed for _index_template/synthetics
{"error":{"root_cause":[{"type":"x_content_parse_exception","reason":"[1:269] [index_template] unknown field [allow_auto_create]"}],"type":"x_content_parse_exception","reason":"[1:269] [index_template] unknown field [allow_auto_create]"},"status":400}`,
    type: 'Index'
  },
  { name: 'logs-191998', status: 'success', type: 'Index' },
  { name: 'logs-201998', status: 'success', type: 'Index' },
  { name: 'logs-211998', status: 'success', type: 'Index' },
  { name: 'daily_logs', status: 'success', type: 'Index Template' },
  { name: 'logs-all', status: 'success', type: 'Alias' }
];

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
  const [errors, setErrors] = useState<string[]>([]);

  const validateSession = useCallback(() => {
    const validationErrors: string[] = [];
    console.log(`*** session info: ${JSON.stringify(session)}`);
    if (session?.snapshot !== 'success') {
      // validationErrors.push(
      //   'Snapshot must be defined before running evaluation.'
      // );
    }
    setErrors(validationErrors);
  }, [session, setErrors]);

  const loadItems = () => {
    setIndexes([]);
    setTimeout(() => {
      setIndexes(allItems);
      setStatus('completed');
    }, 1500);
  };

  const runProcess = () => {
    // if (errors) {
    //   return;
    // }
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
    runProcess();
  }, [validateSession]);

  const renderStatus = () => {
    if (errors.length > 0) {
      return <StatusIndicator type="stopped">Idle</StatusIndicator>;
    }

    switch (status) {
      case 'running':
        return <StatusIndicator type="in-progress">Running</StatusIndicator>;
      case 'completed':
        return <StatusIndicator type="stopped">Idle</StatusIndicator>;
        // return <StatusIndicator type="success">Completed</StatusIndicator>;
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
        columns={2}
        items={[
          { label: 'Status', value: renderStatus() },
          { label: 'Indices', value: allItems.filter(x => x.type === 'Index').length },
          { label: 'Templates', value: allItems.filter(x => x.type === 'Index Template' || x.type === 'Component Template').length },
          { label: 'Aliases', value: allItems.filter(x => x.type === 'Alias').length },
          // {
          //   label: 'Raw Logs',
          //   value: (
          //     <Link href="#" external>
          //       Metadata {mode} logs
          //     </Link>
          //   )
          // }
        ]}
      />

      <SpaceBetween size="s" direction="horizontal">
        <Button
          onClick={runProcess}
          disabled={status === 'running' || errors.length > 0}
        >
          Rerun {mode === 'evaluation' ? 'Evaluation' : 'Migration'}
        </Button>
        {(
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
          <MigrationEntityTable items={indexes} label="Items" mode={mode} />
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
