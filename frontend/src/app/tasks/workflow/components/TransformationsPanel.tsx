import Button from '@cloudscape-design/components/button';
import { TransformationsPanelProps } from '../types';

export function TransformationsPanel({ count, onEdit }: TransformationsPanelProps) {
  return (
    <Button variant="normal" onClick={onEdit}>
      Edit Transformations ({count})
    </Button>
  );
}
