'use client';

import Header from '@cloudscape-design/components/header';
import SpaceBetween from '@cloudscape-design/components/space-between';
import Box from '@cloudscape-design/components/box';
import Icon from '@cloudscape-design/components/icon';
import Popover from '@cloudscape-design/components/popover';
import StatusIndicator from '@cloudscape-design/components/status-indicator';
import styles from './migration-path.module.css';
import Link from 'next/link';
import { ColumnLayout, Grid, KeyValuePairs } from '@cloudscape-design/components';

const checks = [
  {
    id: 'source-connectivity',
    label: 'Source connectivity',
    status: 'success',
    details: 'Successfully connected to source cluster.',
    cluster: 'source'
  },
  {
    id: 'mapping-check',
    label: 'Index mapping validation',
    status: 'warning',
    details: 'Some field types differ between source and target.',
    cluster: 'source'
  },
  {
    id: 'target-health',
    label: 'Target cluster health',
    status: 'error',
    details: 'Target cluster is red. Shards unassigned.',
    cluster: 'target'
  }
];

export default function MigrationPathPage() {
  return (
    <>
      <Header variant="h3">Migration path</Header>
      <Grid
        disableGutters
        gridDefinition={[{ colspan: 4 }, { colspan: 4 }, { colspan: 4 }]}
      >
        <ClusterNode label="Source" version="Elasticsearch 6.8" name="log-data" health="success" clusterId="source" />
        <PathArrow label="Backfill" />
        <ClusterNode label="Target" version="OpenSearch 3.0" name="new-logs-data" health="error" clusterId="target" />
      </Grid>
    </>
  );
}

function ClusterNode({ label, version, name, health, clusterId }) {
  const healthMessages = {
    success: 'Cluster is healthy.',
    warning: 'Cluster has warnings.',
    error: 'Cluster has critical issues.'
  };

  const clusterChecks = checks.filter((check) => check.cluster === clusterId);

  const aggregatedCounts = clusterChecks.reduce(
    (acc, check) => {
      acc[check.status] += 1;
      return acc;
    },
    { success: 0, warning: 0, error: 0 }
  );

  const statusSummary = (
    <SpaceBetween size="xs" direction="horizontal">
      {aggregatedCounts.success > 0 && (
        <StatusIndicator type="success">{aggregatedCounts.success}</StatusIndicator>
      )}
      {aggregatedCounts.warning > 0 && (
        <StatusIndicator type="warning">{aggregatedCounts.warning}</StatusIndicator>
      )}
      {aggregatedCounts.error > 0 && (
        <StatusIndicator type="error">{aggregatedCounts.error}</StatusIndicator>
      )}
    </SpaceBetween>
  );

  return (
    <div className={styles.clusterNodeBox}>
        <KeyValuePairs
          columns={2}
          items={[
          {label: label, value: version, info: (clusterId === 'source' ? <Icon name="multiscreen" /> : <Icon url="opensearch-icon.png" />)},
          {label: 'Status', value: <Popover
            dismissAriaLabel="Close status"
            position="top"
            size="medium"
            triggerType="text"
            content={
              <SpaceBetween size="s">
                <StatusIndicator type={health}>{healthMessages[health]}</StatusIndicator>
                {clusterChecks.map((check) => (
                  <Box key={check.id}>
                    <StatusIndicator type={check.status}>{check.label}</StatusIndicator>
                    <Box variant="p" fontSize="body-s">
                      {check.details}
                    </Box>
                  </Box>
                ))}
              </SpaceBetween>
            }
          >
            {statusSummary}
          </Popover>}
        ]}></KeyValuePairs>
    </div>
  );
}

function PathArrow({ label }) {
  return (
    <div className={styles.pathArrow}>
      <Icon name="arrow-right" />
      <Box variant="small" textAlign="center">
        {label}
      </Box>
    </div>
  );
}