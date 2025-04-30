import Header from '@cloudscape-design/components/header';
import { TaskHeaderProps } from '../types';

export function TaskHeader({ taskId }: TaskHeaderProps) {
  return <Header variant="h1">Task Workflow for {taskId}</Header>;
}
