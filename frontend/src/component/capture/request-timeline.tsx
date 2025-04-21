'use client';

import { useMemo, useState } from 'react';
import {
  Button,
  MixedLineBarChart,
  SpaceBetween
} from '@cloudscape-design/components';
import type { MixedLineBarChartProps } from '@cloudscape-design/components';
import EstimateCompletionTime from '../time/eta';
import DemoWrapper from '../demoWrapper';

export interface RequestPoint {
  timestamp: number;
  requestCount: number;
}

interface RequestTimelineProps {
  proxies: {
    id: number;
    startTime: number;
    requestsAtSecond: number[];
  }[];
  showReplayers: boolean;
}

interface Datum<T> {
  x: T;
  y: number;
}

export default function RequestTimeline({
  proxies,
  showReplayers
}: RequestTimelineProps) {
  const [movingThresholds, setMovingThresholds] = useState<
    { id: string; startTime: number; addedAt: number; multiplier: number }[]
  >([]);
  const [multiplierInput, setMultiplierInput] = useState('1');

  const { chartSeries, totalSeries } = useMemo(() => {
    if (proxies?.length === 0) {
      return {
        chartSeries: [] as MixedLineBarChartProps.DataSeries<Date>[],
        totalSeries: {
          title: 'Total Requests',
          type: 'line',
          data: [] as Datum<Date>[]
        } as MixedLineBarChartProps.DataSeries<Date>
      };
    }

    // 1. Create a map of all timestamps across all proxies
    const timestampMap = new Map<number, number>(); // timestamp => total count

    const chartSeries: MixedLineBarChartProps.DataSeries<Date>[] = proxies?.map(
      (proxy, index) => {
        const dataPoints = proxy.requestsAtSecond.map((val, i) => {
          const timestamp =
            Math.floor((proxy.startTime + i * 1000) / 1000) * 1000; // normalize to full second
          const existing = timestampMap.get(timestamp) || 0;
          timestampMap.set(timestamp, existing + val);
          return {
            x: new Date(timestamp),
            y: val
          };
        });

        return {
          title: `Proxy ${index + 1}`,
          type: 'line',
          data: dataPoints
        };
      }
    );

    // 2. Create total series from the timestampMap
    const totalData = Array.from(timestampMap.entries())
      .sort(([a], [b]) => a - b)
      .map(([ts, val]) => ({
        x: new Date(ts),
        y: val
      }));

    const totalSeries: MixedLineBarChartProps.DataSeries<Date> = {
      title: 'Total Requests',
      type: 'line',
      data: totalData
    };

    return { chartSeries, totalSeries };
  }, [proxies]);

  const now = Date.now();

  const movingThresholdSeries: MixedLineBarChartProps.ThresholdSeries[] =
    movingThresholds
      .map((threshold) => {
        const elapsed = now - threshold.addedAt;
        const virtualTime =
          threshold.startTime + elapsed * threshold.multiplier;
        const thresholdTime = virtualTime < now ? virtualTime : now;
        return {
          type: 'threshold',
          x: new Date(thresholdTime),
          title: `x${threshold.multiplier} Replayer`,
          color: 'purple'
        };
      })
      .filter(Boolean) as MixedLineBarChartProps.ThresholdSeries[];

  const allSeries: MixedLineBarChartProps.ChartSeries<Date>[] = [
    ...chartSeries,
    totalSeries,
    ...movingThresholdSeries
  ];

  // Only use the total series for the demo wrapper analysis
  const allTotalPoints = totalSeries.data;
  const totalRequestCount = allTotalPoints.reduce(
    (sum, point) => sum + point.y,
    0
  );

  const addMovingThreshold = () => {
    const multiplier = parseFloat(multiplierInput);
    if (!isNaN(multiplier) && allTotalPoints.length > 0) {
      const id = `threshold-${Date.now()}`;
      const startTime = allTotalPoints[0].x.getTime();
      const addedAt = Date.now();

      setMovingThresholds((prev) => [
        ...prev,
        {
          id,
          startTime,
          addedAt,
          multiplier
        }
      ]);
    }
  };

  return (
    <SpaceBetween size="m">
      <MixedLineBarChart
        hideFilter={true}
        series={allSeries}
        yTitle="Request Count"
        xTitle="Time"
        height={300}
        statusType="finished"
        xScaleType="time"
        i18nStrings={{}}
        xTickFormatter={(e) => {
          if (!e || !e.toLocaleDateString) return '0';
          return e
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
        yTickFormatter={(e) => e.toString()}
      />

      {showReplayers && (
        <DemoWrapper keyName="playback-controls">
          <SpaceBetween size="xs" direction="horizontal">
            <Button onClick={addMovingThreshold}>Start Replayer</Button>
            <input
              type="number"
              min="0.1"
              step="0.1"
              value={multiplierInput}
              onChange={(e) => setMultiplierInput(e.target.value)}
              style={{ width: '60px' }}
            />
          </SpaceBetween>
        </DemoWrapper>
      )}

      {movingThresholds.map((threshold) => {
        const elapsed = now - threshold.addedAt;
        const virtualTime =
          threshold.startTime + elapsed * threshold.multiplier;
        const thresholdTime = Math.min(virtualTime, now);

        const requests = allTotalPoints
          .filter((r) => r.x.getTime() < thresholdTime)
          .reduce((sum, r) => sum + r.y, 0);

        const requestDelta = totalRequestCount - requests;
        const rateDiff = threshold.multiplier - 1;

        return (
          <div key={threshold.id}>
            <strong>x{threshold.multiplier} Replayer</strong> – Sent:{' '}
            {requests.toLocaleString()} –{' '}
            <EstimateCompletionTime
              etaSeconds={Math.round(requestDelta / rateDiff)}
              variant="inline"
              status="in-progress"
              percentage={requests / totalRequestCount}
            />
          </div>
        );
      })}
    </SpaceBetween>
  );
}
