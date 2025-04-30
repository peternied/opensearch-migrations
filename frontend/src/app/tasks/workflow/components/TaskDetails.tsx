import Box from '@cloudscape-design/components/box';
import { KeyValuePairs, KeyValuePairsProps } from '@cloudscape-design/components';
import { TaskDetailsProps, TaskItem } from '../types';
import { TransformationsPanel } from './TransformationsPanel';

export function TaskDetails({ taskId, items, onEditTransformations }: TaskDetailsProps) {
  // Convert task items to key-value pairs format
  function itemToKvp(item: TaskItem): KeyValuePairsProps.Item {
    return { label: item.name, value: item.status };
  }

  // Create key-value pairs items
  const itemKvp = items.map(itemToKvp);
  
  // Add transformations button
  itemKvp.push({
    label: 'Transformations',
    value: <TransformationsPanel count={3} onEdit={onEditTransformations} />,
  });

  return (
    <>
      <Box variant="h2">Task Details</Box>
      <KeyValuePairs items={itemKvp} columns={3} />
    </>
  );
}
