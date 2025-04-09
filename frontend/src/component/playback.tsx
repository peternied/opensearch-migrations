'use client';

import { useEffect, useRef, useState } from 'react';
import {
  Button,
  Container,
  MixedLineBarChart,
  SpaceBetween
} from '@cloudscape-design/components';
import type { MixedLineBarChartProps } from '@cloudscape-design/components';

export interface RequestPoint {
  timestamp: number; // Unix ms
  requestCount: number;
}

export interface PlaybackMarker {
  timestamp: number;
  label: string;
}

export default function RequestPlaybackTimeline() {
  const [data, setData] = useState<RequestPoint[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [startTime, setStartTime] = useState<number | null>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const maxRequests = 5000;
  const [movingThresholds, setMovingThresholds] = useState<
    { id: string; startTime: number; addedAt: number; multiplier: number }[]
  >([]);

  const [multiplierInput, setMultiplierInput] = useState('1');

  // Start or resume data generation
  const start = () => {
    if (!startTime) {
      const initialTime = Date.now();
      const interval = 5000;

      const firstCount = getRandomCount(0);
      const secondCount = getRandomCount(firstCount);
      const thirdCount = getRandomCount(secondCount);
      const forthCount = getRandomCount(secondCount);

      const initialData: RequestPoint[] = [
        { timestamp: initialTime - 3 * interval, requestCount: firstCount },
        { timestamp: initialTime - 2 * interval, requestCount: secondCount },
        { timestamp: initialTime - 1 * interval, requestCount: thirdCount },
        { timestamp: initialTime - 0 * interval, requestCount: forthCount }
      ];

      setStartTime(initialTime);
      setData(initialData);
    }

    setIsRunning(true);
  };

  // Pause the data generation
  const pause = () => {
    setIsRunning(false);
  };

  // Restart everything
  const restart = () => {
    setIsRunning(false);
    setStartTime(null);
    setData([]);
    setMovingThresholds([]);
  };

  const addMovingThreshold = () => {
    const multiplier = parseFloat(multiplierInput);
    if (!isNaN(multiplier) && data.length > 0) {
      const id = `threshold-${Date.now()}`;
      const startTime = data[0].timestamp;
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

  // Interval for data generation
  useEffect(() => {
    if (isRunning) {
      timerRef.current = setInterval(() => {
        setData((prev) => {
          const last = prev[prev.length - 1];
          const newCount = getRandomCount(last?.requestCount || 0);
          const next = {
            timestamp: Date.now(),
            requestCount: newCount
          };
          return [...prev, next];
        });
      }, 1000);
    }

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isRunning]);

  // Helper: incrementing random values toward 5,000
  const getRandomCount = (last: number) => {
    const maxIncrement = Math.max(500, Math.floor((maxRequests - last) / 10));
    return Math.min(
      maxRequests,
      last + Math.floor(Math.random() * maxIncrement)
    );
  };

  const now = Date.now();
  const movingThresholdSeries: MixedLineBarChartProps.ThresholdSeries[] =
    movingThresholds
      .map((threshold) => {
        const elapsed = now - threshold.addedAt;
        const virtualTime =
          threshold.startTime + elapsed * threshold.multiplier;
        const thresholdTime = virtualTime < now ? virtualTime : now;

        const requests = data
          .filter((r) => r.timestamp < thresholdTime)
          .reduce((sum, r) => sum + r.requestCount, 0);
        return {
          type: 'threshold',
          x: new Date(thresholdTime),
          title:
            `x${threshold.multiplier} Replayer - sent requests ` +
            requests.toLocaleString(),
          color: 'purple'
        };
      })
      .filter(Boolean) as MixedLineBarChartProps.ThresholdSeries[];

  const series: MixedLineBarChartProps.ChartSeries<Date>[] = [
    {
      title: 'Incoming Requests',
      type: 'line',
      data: data.map((d) => ({ x: new Date(d.timestamp), y: d.requestCount }))
    },
    {
      title:
        'Now - captured requests ' +
        data
          .reduce(
            (accumulator, currentValue) =>
              accumulator + currentValue.requestCount,
            0
          )
          .toLocaleString(),
      type: 'threshold',
      x: new Date(),
      color: 'red'
    },
    ...movingThresholdSeries
  ];

  return (
    <SpaceBetween size="m">
      <Container>
        <MixedLineBarChart
          hideFilter={true}
          series={series}
          // xDomain={xDomain}
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
                hour12: false
              })
              .split(',')
              .join('\n');
          }}
          yTickFormatter={(e) => e.toString()}
        />
      </Container>

      <SpaceBetween size="xs" direction="horizontal">
        <Button onClick={start} disabled={isRunning}>
          Start
        </Button>
        <Button onClick={pause} disabled={!isRunning}>
          Pause
        </Button>
        <Button onClick={restart}>Restart</Button>
      </SpaceBetween>
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
    </SpaceBetween>
  );
}
