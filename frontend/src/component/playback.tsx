'use client';

import { useEffect, useState } from 'react';
import LineChart, { LineChartProps } from '@cloudscape-design/components/line-chart';
import { Container, MixedLineBarChartProps } from '@cloudscape-design/components';

export interface RequestPoint {
  timestamp: number; // Unix ms
  requestCount: number;
}

export interface PlaybackMarker {
  timestamp: number;
  label: string;
}

interface RequestPlaybackTimelineProps {
  // data: RequestPoint[];
  // playbackMarkers: PlaybackMarker[];
}

export default function RequestPlaybackTimeline({
  // data,
  // playbackMarkers
}: RequestPlaybackTimelineProps) {
  const data= [
    { timestamp: Date.parse("2025-04-02"), requestCount: 30 },
    { timestamp: Date.parse("2025-04-03"), requestCount: 400 },
    { timestamp: Date.parse("2025-04-04"), requestCount: 8000 },
    { timestamp: Date.parse("2025-04-05"), requestCount: 43000 },
    { timestamp: Date.parse("2025-04-06"), requestCount: 4100 },
    { timestamp: Date.parse("2025-04-07"), requestCount: 200 },
  ]
  const playbackMarkers=[{label: 'Event', timestamp: Date.parse("2025-04-04")}]

  const [now, setNow] = useState(Date.now());

  // Update current time every 5 seconds
  useEffect(() => {
    const interval = setInterval(() => setNow(Date.now()), 5000);
    return () => clearInterval(interval);
  }, []);

  const xDomain = [
    new Date(Math.min(...data.map(d => d.timestamp))),
    new Date(Math.max(...data.map(d => d.timestamp))),
  ];

  const annotations = {
    x: [
      {
        x: xDomain[0],
        label: 'First Request',
        color: 'blue'
      },
      {
        x: new Date(now),
        label: 'Now',
        color: 'red'
      },
      ...playbackMarkers.map(marker => ({
        x: new Date(marker.timestamp),
        label: marker.label,
        color: 'green'
      }))
    ]
  };
  const series: ReadonlyArray<MixedLineBarChartProps.LineDataSeries<Date>> = [
      {
        title: 'Incoming Requests',
        type: 'line',
        data: data.map(d => ({ x: new Date(d.timestamp), y: d.requestCount })),
      }
    ];

  return (
    <Container>
        <LineChart
          series={series}          
          xDomain={xDomain}
          yTitle="Request Count"
          xTitle="Time"
          height={300}
          legendTitle="Legend"
          statusType="finished"
          i18nStrings={{
            filterLabel: 'Filter displayed data ',
            filterPlaceholder: 'Filter data',
            legendAriaLabel: 'Chart legend',
          }}
          xTickFormatter= {e => {
            if (!e || !e.toLocaleDateString) {return "0"; }
            return e.toLocaleDateString("en-US", {
                month: "short",
                day: "numeric",
                hour: "numeric",
                minute: "numeric",
                hour12: !1
              })
              .split(",")
              .join("\n")}
            }
          yTickFormatter={e => e.toString()}
        />
    </Container>
  );
}
