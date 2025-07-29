"use client";

import React, { useEffect, useState } from "react";
import {
  SpaceBetween,
  Header,
  Button,
  Spinner,
} from "@cloudscape-design/components";
import { sessionStatus } from "@/generated/api";
import DebugCommands from "@/components/playground/debug/DebugCommands";
import { useSearchParams } from "next/navigation";
import SessionStatusView from "@/components/session/SessionStatus";


export default function ViewSessionPage() {
  const searchParams = useSearchParams();
  const sessionName = searchParams.get("sessionName");

  const [isReady, setIsReady] = useState(false);
  const [sessionData, setSessionData] = useState<any | null>(null);

  const fetchSession = async () => {
    if (!sessionName) {
      setSessionData({status: "Not Found"});
      setIsReady(true);
      return;
  };
    try {
      const res = await sessionStatus({ path: { session_name: sessionName } });
      if (res.response.status === 200) {
        setSessionData(res.data);
        setIsReady(true);
        return;
      }
    } catch (err) {
      console.error("Error loading session:", err);
    }
    setSessionData(null);
    setIsReady(true);
};

  useEffect(() => {
    fetchSession();
  }, [sessionName]);

  return (
    <SpaceBetween size="m">
      <Header variant="h1">Migration Session - {sessionName}</Header>
        {!isReady && <Spinner size="large"></Spinner>}
        {isReady && <SessionStatusView session={sessionData}></SessionStatusView>}
      <DebugCommands>
        <SpaceBetween size="xs" direction="horizontal">
        <Button onClick={() => fetchSession()}>Reload</Button>
        <Button onClick={() => setIsReady(false)}>Simulate Loading</Button>
          <Button
            onClick={() => {
              setIsReady(false);
              setSessionData(null);
            }}
          >
            Reset
          </Button>
        </SpaceBetween>
      </DebugCommands>
    </SpaceBetween>
  );
}
