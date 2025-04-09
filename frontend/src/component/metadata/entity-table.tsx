'use client';

import { useState } from 'react';
import Table from '@cloudscape-design/components/table';
import Pagination from '@cloudscape-design/components/pagination';
import StatusIndicator from '@cloudscape-design/components/status-indicator';
import Popover from '@cloudscape-design/components/popover';
import { Box, Header, SpaceBetween } from '@cloudscape-design/components';

export interface MigrationEntity {
  name: string;
  status?: 'success' | 'error';
  message?: string;
}

interface MigrationEntityTableProps {
  items: MigrationEntity[];
  label: string;
  pageSize?: number;
  mode: 'evaluation' | 'migration';
}

export default function MigrationEntityTable({
  items,
  label,
  pageSize = 5,
  mode,
}: MigrationEntityTableProps) {
  const [currentPage, setCurrentPage] = useState(1);

  const totalPages = Math.ceil(items.length / pageSize);
  const pagedItems = items.slice((currentPage - 1) * pageSize, currentPage * pageSize);

  if (items.length === 0) {
    return (
      <Box padding={{ vertical: 'l' }}> <SpaceBetween size='m'>
        <Header variant='h3'>{label}</Header>
        <StatusIndicator type="info">None found</StatusIndicator>
        </SpaceBetween>
      </Box>
    );
  }

  return (
    <Table
      columnDefinitions={[
        {
          id: 'name',
          header: 'Name',
          cell: item => item.name,
          width: '70%'
        },
        {
            id: 'status',
            header: 'Status',
            cell: item =>
              item.status === 'success' ? (
                <StatusIndicator type={mode === 'evaluation' ? 'info' : 'success' }>
                    {mode === 'evaluation' ? 'Ready for migration' : 'Successfully migrated'}
                </StatusIndicator>
              ) : item.status === 'error' ? (
                <Popover
                  dismissButton={false}
                  position="top"
                  size="small"
                  triggerType="custom"
                  content={item.message}
                >
                  <StatusIndicator type="error">Failed</StatusIndicator>
                </Popover>
              ) : null,
            minWidth: 120,
            maxWidth: 140,
          },
      ]}
      items={pagedItems}
      variant="embedded"
      header={<Header variant='h3'>{label}</Header>}
      pagination={
        totalPages > 1 ? <Pagination
          currentPageIndex={currentPage}
          pagesCount={totalPages}
          onChange={({ detail }) => setCurrentPage(detail.currentPageIndex)}
        /> : undefined
      }
    />
  );
}
