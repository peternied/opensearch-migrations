'use client';

import Header from '@cloudscape-design/components/header';
import Container from '@cloudscape-design/components/container';
import SpaceBetween from '@cloudscape-design/components/space-between';
import { MigrationSession } from '@/context/migration-session';
import {
  KeyValuePairs,
  LineChart,
  Link,
  MixedLineBarChartProps,
  StatusIndicator
} from '@cloudscape-design/components';

function formatDuration(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  return `${h}h ${m}m ${s}s`;
}

function formatBytes(bytes: number): string {
  const mb = bytes / (1024 * 1024 * 1024);
  return `${mb.toFixed(2)} GB`;
}

function generateSeries(
  durationSeconds: number,
  average: number,
  label: string
): MixedLineBarChartProps.LineDataSeries<number>[] {
  const interval = 300;
  const points = Math.floor(durationSeconds / interval);
  const data = Array.from({ length: points }, (_, i) => ({
    x: new Date(session.createdAt + i * interval * 1000).getTime(),
    y: average + (Math.random() - 0.5) * average * 0.3
  }));
  const result: MixedLineBarChartProps.LineDataSeries<number> = {
    title: label,
    type: 'line',
    data: data
  };
  return [result];
}

// Dummy data – replace with real props or data fetching
const session: MigrationSession = {
  id: 'session-123',
  name: 'April Migration Run',
  createdAt: new Date('2025-04-17T14:00:00Z').getTime(),
  etaSeconds: 86400,
  sizeBytes: 12884901888,
  metadata: 'success',
  metadataDetails: {
    status: 'completed',
    indices: 42,
    templates: 10,
    aliases: 15
  },
  backfill: 'success',
  backfillDetails: {
    status: 'completed',
    durationSeconds: 7200,
    throughputMbPerSec: 75.5,
    sizeBytes: 10884901888,
    docs: '23,420,233'
  },
  replay: 'success',
  replayDetails: {
    status: 'completed',
    toSingularitySeconds: 3600,
    toCutoverSeconds: 1800,
    sizeBytes: 2884901888,
    requests: '342,232,322'
  }
};
const backfillData = generateSeries(
  session.backfillDetails!.durationSeconds,
  session.backfillDetails!.throughputMbPerSec,
  'Throughput'
);

const replayData = generateSeries(
  session.replayDetails!.toSingularitySeconds +
    session.replayDetails!.toCutoverSeconds,
  500 + Math.random() * 100,
  'Replay RPS'
);
export default function MigrationSessionReviewPage() {
  return (
    <SpaceBetween size="l">
      <Container header={<Header variant="h2">Session Overview</Header>}>
        <KeyValuePairs
          columns={3}
          items={[
            {
              label: 'Session',
              value: session.name
            },
            {
              label: 'Created At',
              value: session.createdAt.toLocaleString()
            },
            {
              label: 'Total Size',
              value: formatBytes(session.sizeBytes)
            }
          ]}
        />
      </Container>

      {/* Metadata */}
      <Container header={<Header variant="h2">Metadata</Header>}>
        <KeyValuePairs
          columns={2}
          items={[
            {
              label: 'Status',
              value: <StatusIndicator type={session.metadata}></StatusIndicator>
            },
            {
              label: 'Indices',
              value: session.metadataDetails!.indices
            },
            {
              label: 'Templates',
              value: session.metadataDetails!.templates
            },
            {
              label: 'Aliases',
              value: session.metadataDetails!.aliases
            },
            {
              label: 'Raw Logs',
              value: (
                <Link href="#non-existent" external>
                  Metadata migration logs
                </Link>
              )
            }
          ]}
        />
      </Container>

      {/* Backfill */}
      <Container header={<Header variant="h2">Backfill</Header>}>
        <SpaceBetween size="xxl">
          <KeyValuePairs
            columns={2}
            items={[
              {
                label: 'Status',
                value: (
                  <StatusIndicator type={session.backfill}></StatusIndicator>
                )
              },
              {
                label: 'Transferred',
                value: formatBytes(session.backfillDetails!.sizeBytes)
              },
              {
                label: 'Documents',
                value: session.backfillDetails!.docs
              },
              {
                label: 'Duration',
                value: formatDuration(session.backfillDetails!.durationSeconds)
              },
              {
                label: 'Throughput (MB/sec)',
                value: session.backfillDetails!.throughputMbPerSec.toFixed(2)
              },
              {
                label: 'Raw Logs',
                value: (
                  <Link href="#non-existent" external>
                    96 worker logs
                  </Link>
                )
              }
            ]}
          />
          <LineChart
            series={backfillData}
            xTitle="Time"
            yTitle="MB/sec"
            height={250}
            ariaLabel="Backfill Throughput"
            hideLegend={true}
            hideFilter={true}
            xTickFormatter={(e) => {
              const d = new Date(e);
              return d
                .toLocaleDateString('en-US', {
                  month: 'short',
                  day: 'numeric',
                  hour: 'numeric',
                  minute: 'numeric',
                  second: 'numeric',
                  hour12: true
                })
                .split(',')
                .join('\n');
            }}
          />
        </SpaceBetween>
      </Container>

      {/* Replay */}
      <Container header={<Header variant="h2">Replay</Header>}>
        <SpaceBetween size="xxl">
          <KeyValuePairs
            columns={2}
            items={[
              {
                label: 'Status',
                value: <StatusIndicator type={session.replay}></StatusIndicator>
              },
              {
                label: 'Transferred',
                value: formatBytes(session.replayDetails!.sizeBytes)
              },
              {
                label: 'Replayed Requests',
                value: session.replayDetails!.requests
              },
              {
                label: 'Start to Singularity',
                value: formatDuration(
                  session.replayDetails!.toSingularitySeconds
                )
              },
              {
                label: 'Singularity to Cutover',
                value: formatDuration(session.replayDetails!.toCutoverSeconds)
              },
              {
                label: 'Tuple Logs',
                value: (
                  <Link href="#non-existent" external>
                    342,232,322 tuples entries
                  </Link>
                )
              },
              {
                label: 'Raw Logs',
                value: (
                  <Link href="#non-existent" external>
                    Replayer process logs
                  </Link>
                )
              }
            ]}
          />
          <LineChart
            series={replayData}
            xTitle="Time"
            yTitle="Requests/sec"
            height={250}
            ariaLabel="Replay Request Rate"
            hideLegend={true}
            hideFilter={true}
            xTickFormatter={(e) => {
              const d = new Date(e);
              return d
                .toLocaleDateString('en-US', {
                  month: 'short',
                  day: 'numeric',
                  hour: 'numeric',
                  minute: 'numeric',
                  second: 'numeric',
                  hour12: true
                })
                .split(',')
                .join('\n');
            }}
          />
        </SpaceBetween>
      </Container>
    </SpaceBetween>
  );
}
