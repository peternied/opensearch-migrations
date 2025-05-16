import Button from '@cloudscape-design/components/button';
import { TransformationsPanelProps } from '../types';

export function TransformationsPanel({
  count,
  onEdit
}: TransformationsPanelProps) {
  return (
    <Button variant="inline-link" onClick={onEdit} iconName='edit'>
      Modify ({count})
    </Button>
  );
}
