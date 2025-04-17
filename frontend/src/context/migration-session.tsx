// context/migration-session-context.tsx
'use client';

import { createContext, useContext, useState, ReactNode } from 'react';

export interface MigrationSession {
  id: string;
  name: string;
  status: 'pending' | 'running' | 'completed';
  createdAt: string;
}

const initialSessions: MigrationSession[] = [
  {
    id: 'session-1',
    name: 'Initial Test Migration',
    status: 'completed',
    createdAt: new Date().toISOString()
  },
  {
    id: 'session-2',
    name: 'Ongoing Migration Session',
    status: 'running',
    createdAt: new Date().toISOString()
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
