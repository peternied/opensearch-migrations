'use client';

import { useState, useEffect } from 'react';
import {
  Header,
  Container,
  SpaceBetween,
  Button,
  Box,
  CopyToClipboard,
  KeyValuePairs,
  StatusIndicator,
  Tabs
} from '@cloudscape-design/components';
import RequestTimeline from './request-timeline';
import DemoWrapper from '../demoWrapper';
import Connection from '../connection/remote-connection';

interface ProxyInstance {
  id: number;
  startTime: number;
  requestsAtSecond: number[];
}

const LOAD_BALANCER_URL = 'https://k8.deployed/capture-proxy';

export default function CaptureProxiesOverview() {
  const [activeTabId, setActiveTabId] = useState('managed');
  const [proxies, setProxies] = useState<ProxyInstance[]>([]);
  const [isDeploying, setIsDeploying] = useState(false);
  const [deploymentComplete, setDeploymentComplete] = useState(false);

  useEffect(() => {
    const interval = setInterval(() => {
      setProxies((prev) =>
        prev.map((proxy) => ({
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

  useEffect(() => {
    if (isDeploying) {
      setTimeout(() => {
        setDeploymentComplete(true);
        setIsDeploying(false);
        const newProxies = Array.from({ length: 3 }, (_, i) => ({
          id: i,
          startTime: Date.now(),
          requestsAtSecond: []
        }));
        setProxies((prev) => [...prev, ...newProxies]);
      }, 1000);
    }
  }, [isDeploying]);

  const handleDeployClick = () => {
    setIsDeploying(true);
    setDeploymentComplete(false);
  };

  const handleAddProxyClick = () => {
    const newProxy: ProxyInstance = {
      id: Date.now(),
      startTime: Date.now(),
      requestsAtSecond: []
    };
    setProxies((prev) => [...prev, newProxy]);
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
              label: 'Capture proxy status',
              value: proxies.length ? 'Active' : 'Inactive'
            },
            {
              label: 'Total Requests Captured',
              value: totalRequests.toLocaleString()
            }
          ]}
        />
      </Container>

      <Container
        header={<Header variant="h2">Captured Request Activity</Header>}
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

      <Container header={<Header>Connect Proxies</Header>}>
        <Box>
          Traffic is captured for Migration Assistant through proxies. These can
          be deployed by Migration Assistant and then you would update your
          clusters traffic to the endpoint or they can be manually deployed and
          configured to point to the Migration Assistant system.
        </Box>
        <Tabs
          activeTabId={activeTabId}
          onChange={({ detail }) => setActiveTabId(detail.activeTabId)}
          tabs={[
            {
              id: 'managed',
              label: 'Autoscale Proxies',
              content: (
                <SpaceBetween size="m">
                  <Header variant="h2">Deploy Autoscale Proxies</Header>
                  <Box>
                    Autoscale proxies are managed by Migration Assistant and all
                    traffic passed to the endpoint url will automatically be
                    forward to the source cluster.
                  </Box>
                  <Connection connectionType="source"></Connection>
                  {!deploymentComplete ? (
                    <>
                      <Button
                        disabled={isDeploying}
                        loading={isDeploying}
                        onClick={handleDeployClick}
                      >
                        Deploy Managed Proxy Workers
                      </Button>
                      {isDeploying && (
                        <StatusIndicator type="in-progress">
                          Deploying workers...
                        </StatusIndicator>
                      )}
                    </>
                  ) : (
                    <>
                      <StatusIndicator type="success">
                        Proxy Workers Deployed
                      </StatusIndicator>
                      <Box variant="p">
                        Load balancer endpoint:{' '}
                        <CopyToClipboard
                          textToCopy={LOAD_BALANCER_URL}
                          copySuccessText="Copied"
                          copyErrorText="Unable to copy"
                          variant="inline"
                        />
                      </Box>
                      <Box variant="p">
                        <strong>Next step:</strong> Point your cluster traffic
                        to the load balancer URL above.
                      </Box>
                    </>
                  )}
                </SpaceBetween>
              )
            },
            {
              id: 'manual',
              label: 'Manually Configured Proxies',
              content: (
                <SpaceBetween size="s">
                  <Header variant="h2">Manually Add Proxy</Header>
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
                      Verify the new port is active (e.g.{' '}
                      <code>curl localhost:19200</code>).
                    </li>
                    <li>
                      Ensure <code>JAVA_HOME</code> is set. Use the bundled JDK
                      if needed.
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
                      <Box variant="code">
                        ./trafficCaptureProxyServer --kafkaConnection kafka:9092
                        --destinationUri http://localhost:19200 --listenPort
                        9200 --insecureDestination
                      </Box>
                    </li>
                    <li>
                      Test traffic on both ports (9200, 19200) and verify Kafka
                      topic creation.
                    </li>
                  </ol>
                  <DemoWrapper>
                    <Button onClick={handleAddProxyClick}>
                      Add Manual Proxy
                    </Button>
                  </DemoWrapper>
                </SpaceBetween>
              )
            }
          ]}
        />
      </Container>
    </SpaceBetween>
  );
}
