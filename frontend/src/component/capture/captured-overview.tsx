'use client';

import { useState, useEffect } from 'react';
import Header from '@cloudscape-design/components/header';
import Container from '@cloudscape-design/components/container';
import SpaceBetween from '@cloudscape-design/components/space-between';
import Button from '@cloudscape-design/components/button';
import Box from '@cloudscape-design/components/box';
import { KeyValuePairs, StatusIndicator } from '@cloudscape-design/components';
import RequestTimeline from './request-timeline';
import DemoWrapper from '../demoWrapper';

interface ProxyInstance {
  id: number;
  startTime: number;
  requestsAtSecond: number[]; // represents seconds -after- the start time
}

export default function CaptureProxiesOverview() {
  const [proxies, setProxies] = useState<ProxyInstance[]>([]);
  const [showAddProxy, setShowAddProxy] = useState(false);

  // Simulate 1s updates to proxy RPS data
  useEffect(() => {
    const interval = setInterval(() => {
      setProxies((prevProxies) =>
        prevProxies.map((proxy) => ({
          ...proxy,
          requestsAtSecond: [
            ...proxy.requestsAtSecond,
            Math.floor(Math.random() * 91) + 10
          ]
        }))
      );
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  const handleAddProxyClick = () => {
    const newProxy: ProxyInstance = {
      id: Date.now(),
      startTime: Date.now(),
      requestsAtSecond: []
    };
    setProxies((prev) => [...prev, newProxy]);
  };

  const handleToggleInstallInfo = () => {
    setShowAddProxy((prev) => !prev);
  };

  const totalRequests = proxies.reduce(
    (acc, proxy) => acc + proxy.requestsAtSecond.reduce((a, b) => a + b, 0),
    0
  );

  return (
    <SpaceBetween size="m">
      <Container header={<Header variant="h2">Overview</Header>}>
        <KeyValuePairs
          columns={2}
          items={[
            {
              label: 'Connected Proxies',
              value: `${proxies.length}`
            },
            {
              label: 'Total Requests Captured',
              value: totalRequests.toLocaleString()
            }
          ]}
        />
      </Container>

      <Container
        header={<Header variant="h2">Request Activity Timeline</Header>}
      >
        {proxies.length === 0 ? (
          <Box variant="p">
            No capture proxies connected. Add one below or follow the
            instructions to install a proxy.
          </Box>
        ) : (
          <RequestTimeline proxies={proxies} showReplayers={false} />
        )}
      </Container>

      <Container
        header={<Header variant="h2">Deploy capture proxy workers</Header>}
      >
        <SpaceBetween size="m">
          <Button>Magically do this</Button> {/* TODO: Expand on this */}
          <StatusIndicator type="in-progress">
            Workers deploying
          </StatusIndicator>
        </SpaceBetween>
      </Container>

      <Container
        header={
          <Header
            variant="h2"
            actions={
              <Button onClick={handleToggleInstallInfo} variant="link">
                {showAddProxy ? 'Hide Install Info' : 'Show Install Info'}
              </Button>
            }
          >
            Add proxy instructions
          </Header>
        }
      >
        {showAddProxy && (
          <SpaceBetween size="s">
            <ol style={{ paddingLeft: '1.25rem' }}>
              <li>
                Log into a coordinator node and locate your OpenSearch
                directory.
              </li>
              <li>
                Update the config file to set a new internal port, e.g.{' '}
                <code>http.port: 19200</code>, then restart the node.
              </li>
              <li>
                Verify the new port is active (e.g. <code>netstat</code>,{' '}
                <code>curl localhost:19200</code>).
              </li>
              <li>
                Ensure <code>JAVA_HOME</code> is set. Use the bundled JDK if
                needed.
              </li>
              <li>
                Download the Capture Proxy from{' '}
                <a
                  href="https://github.com/opensearch-project/opensearch-migrations/releases/latest"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  the latest releases
                </a>{' '}
                and extract it.
              </li>
              <li>
                Start the proxy with:
                <Box variant="code" padding={{ top: 'xxs' }}>
                  ./trafficCaptureProxyServer --kafkaConnection kafka:9092
                  --destinationUri http://localhost:19200 --listenPort 9200
                  --insecureDestination
                </Box>
              </li>
              <li>
                Test traffic on both ports (9200, 19200) and verify Kafka topic
                creation.
              </li>
            </ol>
          </SpaceBetween>
        )}
      </Container>

      <DemoWrapper keyName="proxy-controls">
        <SpaceBetween size="s">
          <Button onClick={handleAddProxyClick}>Add Proxy Instance</Button>
        </SpaceBetween>
      </DemoWrapper>
    </SpaceBetween>
  );
}
