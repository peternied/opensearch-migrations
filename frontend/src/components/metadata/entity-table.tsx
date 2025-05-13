'use client';

import Table, { TableProps } from '@cloudscape-design/components/table';
import StatusIndicator, {
  StatusIndicatorProps
} from '@cloudscape-design/components/status-indicator';
import Popover from '@cloudscape-design/components/popover';
import { Box, Header, Link, TextFilter } from '@cloudscape-design/components';
import { useCollection } from '@cloudscape-design/collection-hooks';

export interface MigrationEntity {
  name: string;
  type:
    | 'Index'
    | 'Alias'
    | 'Index Template'
    | 'Component Template'
  status:
    | 'success'
    | 'already-exists'
    | 'transform-failure'
    | 'target-failure'
    | 'incompatible-replica-count'
    | 'skipped-by-filter';
  message?: string;
}

type TableMode = 'evaluation' | 'migration';

interface MigrationEntityTableProps {
  items: MigrationEntity[];
  label: string;
  mode: TableMode;
}

function formatStatus(
  item: MigrationEntity,
  mode: TableMode
): StatusIndicatorProps.Type {
  if (item.status === 'success') {
    return mode === 'evaluation' ? 'in-progress' : 'success';
  }
  if (item.status === 'already-exists') {
    return 'stopped';
  }
  if (item.status === 'skipped-by-filter') {
    return 'pending';
  }
  return 'error';
}

const MIN_ITEM_COUNT_FOR_FILTERING = 3;

export default function MigrationEntityTable({
  items,
  label,
  mode
}: MigrationEntityTableProps) {
  const collection = useCollection(items, {
    filtering: {
      empty: <StatusIndicator type="info">None found</StatusIndicator>,
      noMatch: <Box>No items with filter criteria.</Box>
    },
    sorting: {}
  });

  const columns: TableProps.ColumnDefinition<MigrationEntity>[] = [
    {
      id: 'status-icon',
      header: '',
      cell: (item) => (
        <StatusIndicator type={formatStatus(item, mode)}></StatusIndicator>
      ),
      width: '3%'
    },
    {
      id: 'entity-type',
      header: 'Type',
      cell: (item) => item.type
    },
    {
      id: 'name',
      header: 'Name',
      cell: (item) => item.name,
      sortingField: 'name'
    },
    {
      id: 'status',
      header: 'Status',
      cell: (item) => item.status
    },
    {
      id: 'message',
      header: 'Message',
      cell: (item) => (item?.message &&
        <Popover
          triggerType={'text'}
          content={item?.message}
        >{item?.message?.substring(0, 80)}</Popover>
      ),
      sortingField: 'message'
    },
    // {
    //   id: 'drill-down',
    //   header: 'Drill Down',
    //   cell: (item) => (
    //     <Popover
    //       content={
    //         <Box>
    //           {`GET /${label}/${item.name}`}
    //           <pre>
    //             {JSON.stringify(JSON.parse('{ "foo": "bar" }'), null, 3)}
    //           </pre>
    //         </Box>
    //       }
    //     >
    //       <Link>{`GET /${label}/${item.name}`}</Link>
    //     </Popover>
    //   )
    // }
  ];
  return (
    <Table
      columnDefinitions={columns}
      {...collection.collectionProps}
      items={collection.items}
      variant="embedded"
      header={<Header variant="h3">{label}</Header>}
      filter={
        collection.items.length > MIN_ITEM_COUNT_FOR_FILTERING && (
          <TextFilter {...collection.filterProps}></TextFilter>
        )
      }
    />
  );
}
