'use client';

import { Status } from '@/components/time/eta';
import { createContext, useContext, useState, ReactNode } from 'react';

export interface MetadataDetails {
  status: string;
  indices: number;
  templates: number;
  aliases: number;
}
export interface BackfillDetails {
  status: string;
  durationSeconds: number;
  throughputMbPerSec: number;
  sizeBytes: number;
  docs: string;
}
export interface ReplayDetails {
  status: string;
  toSingularitySeconds: number;
  toCutoverSeconds: number;
  sizeBytes: number;
  requests: string;
}

export type SessionWorkflow = 'freeform' | 'backfill' | 'replay' | 'full';

export interface MigrationSession {
  id: string;
  name: string;
  createdAt: number;
  metadata: Status;
  metadataDetails?: MetadataDetails;
  backfill: Status;
  backfillDetails?: BackfillDetails;
  replay: Status;
  replayDetails?: ReplayDetails;
  etaSeconds: number | null;
  sizeBytes: number;
  workflow: SessionWorkflow;
}

const GB = 1024 * 1024 * 1024;
const MB = 1024 * 1024;

const demoSessions: MigrationSession[] = [
  {
    id: 'alpha',
    name: 'Session Alpha',
    createdAt: new Date('2024-05-01').getTime(),
    metadata: 'success',
    backfill: 'success',
    replay: 'in-progress',
    etaSeconds: 60 * 60 * 3,
    sizeBytes: 1.2 * GB,
    workflow: 'freeform'
  },
  {
    id: 'beta',
    name: 'Session Beta',
    createdAt: new Date('2024-04-18').getTime(),
    metadata: 'success',
    backfill: 'pending',
    replay: 'pending',
    etaSeconds: null,
    sizeBytes: 0,
    workflow: 'freeform'
  },
  {
    id: 'gamma',
    name: 'Session Gamma',
    createdAt: new Date('2024-05-05').getTime(),
    metadata: 'success',
    backfill: 'in-progress',
    replay: 'pending',
    etaSeconds: 55 * 60,
    sizeBytes: 850 * MB,
    workflow: 'freeform'
  },
  {
    id: 'delta',
    name: 'Session Delta',
    createdAt: new Date('2024-04-30').getTime(),
    metadata: 'pending',
    backfill: 'pending',
    replay: 'pending',
    etaSeconds: null,
    sizeBytes: 0,
    workflow: 'freeform'
  },
  {
    id: 'epsilon',
    name: 'Session Epsilon',
    createdAt: new Date('2024-05-10').getTime(),
    metadata: 'error',
    backfill: 'pending',
    replay: 'pending',
    etaSeconds: null,
    sizeBytes: 0,
    workflow: 'freeform'
  },
  {
    id: 'zeta',
    name: 'Session Zeta',
    createdAt: new Date('2024-04-25').getTime(),
    metadata: 'success',
    backfill: 'success',
    replay: 'success',
    etaSeconds: 0,
    sizeBytes: 3.5 * GB,
    workflow: 'freeform'
  },
  {
    id: 'omega',
    name: 'Session Omega',
    createdAt: new Date('2024-05-03').getTime(),
    metadata: 'success',
    backfill: 'in-progress',
    replay: 'in-progress',
    etaSeconds: 60 * 60 * 1.5,
    sizeBytes: 2.1 * GB,
    workflow: 'freeform'
  },
  {
    id: 'theta',
    name: 'Session Theta',
    createdAt: new Date('2024-04-15').getTime(),
    metadata: 'success',
    backfill: 'error',
    replay: 'pending',
    etaSeconds: null,
    sizeBytes: 500 * MB,
    workflow: 'freeform'
  },
  {
    id: 'iota',
    name: 'Session Iota',
    createdAt: new Date('2024-04-28').getTime(),
    metadata: 'success',
    backfill: 'success',
    replay: 'error',
    etaSeconds: null,
    sizeBytes: 1.8 * GB,
    workflow: 'freeform'
  },
  {
    id: 'kappa',
    name: 'Session Kappa',
    createdAt: new Date('2024-05-07').getTime(),
    metadata: 'success',
    backfill: 'success',
    replay: 'in-progress',
    etaSeconds: 60 * 60 * 2,
    sizeBytes: 2.9 * GB,
    workflow: 'freeform'
  },
  {
    id: 'lambda',
    name: 'Session Lambda',
    createdAt: new Date('2024-04-22').getTime(),
    metadata: 'success',
    backfill: 'pending',
    replay: 'pending',
    etaSeconds: null,
    sizeBytes: 0,
    workflow: 'freeform'
  },
  {
    id: 'mu',
    name: 'Session Mu',
    createdAt: new Date('2024-05-02').getTime(),
    metadata: 'success',
    backfill: 'in-progress',
    replay: 'in-progress',
    etaSeconds: 60 * 60 * 4,
    sizeBytes: 4.4 * GB,
    workflow: 'freeform'
  }
];

import { useEffect } from 'react';

const SESSION_STORAGE_KEY = 'migrationSessions';

function loadSessionsFromLocalStorage(): MigrationSession[] {
  if (typeof window === 'undefined') return [];
  try {
    const stored = localStorage.getItem(SESSION_STORAGE_KEY);
    return stored ? JSON.parse(stored) : [];
  } catch (e) {
    console.warn('Failed to load sessions from localStorage', e);
    return [];
  }
}

function saveSessionsToLocalStorage(sessions: MigrationSession[]) {
  try {
    localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(sessions));
  } catch (e) {
    console.warn('Failed to save sessions to localStorage', e);
  }
}

interface MigrationSessionContextType {
  sessions: MigrationSession[];
  addSession: (session: MigrationSession) => void;
  addDemoSessions: () => void;
  clearSessions: () => void;
}

const MigrationSessionContext = createContext<
  MigrationSessionContextType | undefined
>(undefined);

function useInitializeSessions() {
  const [sessions, setSessions] = useState<MigrationSession[]>([]);
  const [initialized, setInitialized] = useState(false);

  useEffect(() => {
    const loaded = loadSessionsFromLocalStorage();
    setSessions(loaded);
    setInitialized(true);
  }, []);

  useEffect(() => {
    if (initialized) {
      saveSessionsToLocalStorage(sessions);
    }
  }, [sessions, initialized]);

  return { sessions, setSessions, initialized };
}

export function MigrationSessionProvider({
  children
}: {
  children: ReactNode;
}) {
  const { sessions, setSessions } = useInitializeSessions();

  const addSession = (session: MigrationSession) => {
    setSessions((prev) => [...prev, session]);
  };

  const addDemoSessions = () => {
    demoSessions.forEach(addSession);
  };

  const clearSessions = () => {
    setSessions([]);
  };

  return (
    <MigrationSessionContext.Provider
      value={{ sessions, addSession, addDemoSessions, clearSessions }}
    >
      {children}
    </MigrationSessionContext.Provider>
  );
}

export function useMigrationSessions() {
  const context = useContext(MigrationSessionContext);
  if (!context) {
    throw new Error(
      'useMigrationSessions must be used within a MigrationSessionProvider'
    );
  }
  return context;
}
