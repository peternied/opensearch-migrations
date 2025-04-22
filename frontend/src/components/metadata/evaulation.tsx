'use client';

import { useEffect, useState } from 'react';
import Header from '@cloudscape-design/components/header';
import SpaceBetween from '@cloudscape-design/components/space-between';
import StatusIndicator from '@cloudscape-design/components/status-indicator';
import Link from '@cloudscape-design/components/link';
import Button from '@cloudscape-design/components/button';
import KeyValuePairs from '@cloudscape-design/components/key-value-pairs';
import MigrationEntityTable, { MigrationEntity } from './entity-table';
import { Spinner } from '@cloudscape-design/components';

const allIndexes: MigrationEntity[] = [
  { name: 'geonames', status: 'success' },
  { name: 'nyc_taxis', status: 'success' },
  { name: 'percolator', status: 'success' },
  {
    name: 'logs-181998',
    status: 'target-failure',
    message: 'IndexMappingTypeRemoval unsupported. Specify --multi-type-behavior.'
  },
  { name: 'logs-191998', status: 'success' },
  { name: 'logs-201998', status: 'success' },
  { name: 'logs-211998', status: 'success' }
];
const allIndexTemplates: MigrationEntity[] = [
  { name: 'daily_logs', status: 'success' }
];
const allComponentTemplates: MigrationEntity[] = [];
const allAliases: MigrationEntity[] = [
  { name: 'logs-all', status: 'success' }
];

export default function MetadataEvaluationAndMigration() {
  const [mode, setMode] = useState<'evaluation' | 'migration'>('evaluation');
  const [status, setStatus] = useState<'idle' | 'running' | 'completed'>('completed');
  const [indexes, setIndexes] = useState<MigrationEntity[]>([]);
  const [indexTemplates, setIndexTemplates] = useState<MigrationEntity[]>([]);
  const [componentTemplates, setComponentTemplates] = useState<MigrationEntity[]>([]);
  const [aliases, setAliases] = useState<MigrationEntity[]>([]);

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
    setStatus('running');
    loadItems();
  };

  const toggleMode = () => {
    setMode((prev) => (prev === 'evaluation' ? 'migration' : 'evaluation'));
    setStatus('running');
    loadItems();
  };

  useEffect(() => {
    runProcess();
  }, []);

  const renderStatus = () => {
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
      <Header variant="h1">Metadata {mode === 'evaluation' ? 'Evaluation' : 'Migration'}</Header>

      <KeyValuePairs
        columns={3}
        items={[
          { label: 'Status', value: renderStatus() },
          { label: 'Indices', value: indexes.length },
          { label: 'Templates', value: indexTemplates.length },
          { label: 'Aliases', value: aliases.length },
          {
            label: 'Raw Logs',
            value: <Link href="#" external>Metadata {mode} logs</Link>
          }
        ]}
      />

      <SpaceBetween size="s" direction="horizontal">
        <Button onClick={runProcess} disabled={status === 'running'}>
          Rerun {mode === 'evaluation' ? 'Evaluation' : 'Migration'}
        </Button>
        {mode === 'evaluation' && (
          <Button variant="primary" onClick={toggleMode} disabled={status === 'running'}>
            Migrate Items
          </Button>
        )}
      </SpaceBetween>

      {status === 'completed' ? (
        <>
          <MigrationEntityTable items={indexes} label="Indexes" mode={mode} />
          <MigrationEntityTable items={indexTemplates} label="Index Templates" mode={mode} />
          <MigrationEntityTable items={componentTemplates} label="Component Templates" mode={mode} />
          <MigrationEntityTable items={aliases} label="Aliases" mode={mode} />
        </>
      ) : (
        <>
          <Spinner></Spinner> Loading results...
        </>
      )}
    </SpaceBetween>
  );
}

