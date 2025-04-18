'use client';

import { Status } from '@/component/time/eta';
import { createContext, useContext, useState, ReactNode } from 'react';

export interface MigrationSession {
  id: string;
  name: string;
  createdAt: Date;
  metadata: Status;
  metadataDetails?: any;
  backfill: Status;
  backfillDetails?: any;
  replay: Status;
  replayDetails?: any;
  etaSeconds: number | null;
  sizeBytes: number;
}

const GB = 1024 * 1024 * 1024;
const MB = 1024 * 1024;

const initialSessions: MigrationSession[] = [
  {
    id: 'alpha',
    name: 'Session Alpha',
    createdAt: new Date('2024-05-01'),
    metadata: 'success',
    backfill: 'success',
    replay: 'in-progress',
    etaSeconds: 60 * 60 * 3,
    sizeBytes: 1.2 * GB
  },
  {
    id: 'beta',
    name: 'Session Beta',
    createdAt: new Date('2024-04-18'),
    metadata: 'success',
    backfill: 'pending',
    replay: 'pending',
    etaSeconds: null,
    sizeBytes: 0
  },
  {
    id: 'gamma',
    name: 'Session Gamma',
    createdAt: new Date('2024-05-05'),
    metadata: 'success',
    backfill: 'in-progress',
    replay: 'pending',
    etaSeconds: 55 * 60,
    sizeBytes: 850 * MB
  },
  {
    id: 'delta',
    name: 'Session Delta',
    createdAt: new Date('2024-04-30'),
    metadata: 'pending',
    backfill: 'pending',
    replay: 'pending',
    etaSeconds: null,
    sizeBytes: 0
  },
  {
    id: 'epsilon',
    name: 'Session Epsilon',
    createdAt: new Date('2024-05-10'),
    metadata: 'error',
    backfill: 'pending',
    replay: 'pending',
    etaSeconds: null,
    sizeBytes: 0
  },
  {
    id: 'zeta',
    name: 'Session Zeta',
    createdAt: new Date('2024-04-25'),
    metadata: 'success',
    backfill: 'success',
    replay: 'success',
    etaSeconds: 0,
    sizeBytes: 3.5 * GB
  },
  {
    id: 'omega',
    name: 'Session Omega',
    createdAt: new Date('2024-05-03'),
    metadata: 'success',
    backfill: 'in-progress',
    replay: 'in-progress',
    etaSeconds: 60 * 60 * 1.5,
    sizeBytes: 2.1 * GB
  },
  {
    id: 'theta',
    name: 'Session Theta',
    createdAt: new Date('2024-04-15'),
    metadata: 'success',
    backfill: 'error',
    replay: 'pending',
    etaSeconds: null,
    sizeBytes: 500 * MB
  },
  {
    id: 'iota',
    name: 'Session Iota',
    createdAt: new Date('2024-04-28'),
    metadata: 'success',
    backfill: 'success',
    replay: 'error',
    etaSeconds: null,
    sizeBytes: 1.8 * GB
  },
  {
    id: 'kappa',
    name: 'Session Kappa',
    createdAt: new Date('2024-05-07'),
    metadata: 'success',
    backfill: 'success',
    replay: 'in-progress',
    etaSeconds: 60 * 60 * 2,
    sizeBytes: 2.9 * GB
  },
  {
    id: 'lambda',
    name: 'Session Lambda',
    createdAt: new Date('2024-04-22'),
    metadata: 'success',
    backfill: 'pending',
    replay: 'pending',
    etaSeconds: null,
    sizeBytes: 0
  },
  {
    id: 'mu',
    name: 'Session Mu',
    createdAt: new Date('2024-05-02'),
    metadata: 'success',
    backfill: 'in-progress',
    replay: 'in-progress',
    etaSeconds: 60 * 60 * 4,
    sizeBytes: 4.4 * GB
  }
];

interface MigrationSessionContextType {
  sessions: MigrationSession[];
  addSession: (session: MigrationSession) => void;
}

const MigrationSessionContext = createContext<
  MigrationSessionContextType | undefined
>(undefined);

export function MigrationSessionProvider({
  children
}: {
  children: ReactNode;
}) {
  const [sessions, setSessions] = useState<MigrationSession[]>(initialSessions);

  const addSession = (session: MigrationSession) => {
    setSessions((prev) => [...prev, session]);
  };

  return (
    <MigrationSessionContext.Provider value={{ sessions, addSession }}>
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
