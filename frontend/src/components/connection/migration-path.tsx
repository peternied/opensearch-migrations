'use client';

import Container from '@cloudscape-design/components/container';
import Header from '@cloudscape-design/components/header';
import SpaceBetween from '@cloudscape-design/components/space-between';
import Box from '@cloudscape-design/components/box';
import Icon from '@cloudscape-design/components/icon';
import Popover from '@cloudscape-design/components/popover';
import StatusIndicator from '@cloudscape-design/components/status-indicator';
import styles from './migration-path.module.css';
import Link from 'next/link';

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
    <SpaceBetween size="l">
      <Header variant="h3">Migration path</Header>

      <Container>
        <div className={styles.pathContainer}>
          <ClusterNode label="Source: Elasticsearch 6.8" name="log-data" health="success" clusterId="source" />
          <PathArrow label="Backfill" />
          <ClusterNode label="Target: OpenSearch 3.0" name="new-logs-data" health="error" clusterId="target" />
        </div>
      </Container>
    </SpaceBetween>
  );
}

function ClusterNode({ label, name, health, clusterId }) {
  const healthMessages = {
    success: 'Cluster is healthy.',
    warning: 'Cluster has warnings.',
    error: 'Cluster has critical issues.'
  };

  const clusterChecks = checks.filter(check => check.cluster === clusterId);

  return (
    <div className={styles.clusterNodeBox}>
      {clusterId === "source"
        ? <Icon size="big" name='multiscreen'/>
        : <Icon size="big" url='opensearch-icon.png'/>
      }
      <Box variant="strong" margin={{ top: 'xs' }}>{label}</Box>
      <Link href="#">{name}</Link>
      <Popover
        dismissAriaLabel="Close status"
        position="top"
        size="medium"
        triggerType="text"
        content={
          <SpaceBetween size="s">
            <StatusIndicator type={health}>{healthMessages[health]}</StatusIndicator>
            {clusterChecks.map(check => (
              <Box key={check.id}>
                <StatusIndicator type={check.status}>{check.label}</StatusIndicator>
                <Box variant="p" fontSize="body-s">{check.details}</Box>
              </Box>
            ))}
          </SpaceBetween>
        }
      >
        <Box className={styles.statusTrigger}>
          <StatusIndicator type={health}>
            {healthMessages[health]}
          </StatusIndicator>
        </Box>
      </Popover>
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
