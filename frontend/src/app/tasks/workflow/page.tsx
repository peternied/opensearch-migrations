'use client';

import { useParams, useRouter } from 'next/navigation';
import SpaceBetween from '@cloudscape-design/components/space-between';
import Container from '@cloudscape-design/components/container';
import { TaskHeader, TaskDetails, WorkflowProgress } from './components';
import { useWorkflow } from './hooks/useWorkflow';
import { TaskItem } from './types';

// Mock data for associated items - in a real app, this would come from the API
const associatedItems: TaskItem[] = [
  { id: '1', name: 'Index a', status: 'Pending' },
  { id: '2', name: 'Index b', status: 'Migrated' },
  { id: '3', name: 'Index c', status: 'Error' }
];

export default function TaskWorkflowPage() {
  // Get taskId from URL params
  const params = useParams();
  const taskId = (params.taskId as string) || 'Indices (a,b,c)'; // Default to '1' if not provided
  const router = useRouter();

  // Use our custom workflow hook to manage workflow state
  const [workflowState, workflowActions] = useWorkflow(taskId);

  // Event handlers
  const handleEditTransformations = () => {
    alert('Edit transformations clicked!');
  };

  const handleWorkflowComplete = () => {
    workflowActions.completeWorkflow();
    alert(`Task ${taskId} workflow complete!`);
    router.push('/tasks/manage');
  };

  const handleStepChange = (stepIndex: number) => {
    workflowActions.goToStep(stepIndex);
  };

  // Show loading state while data is being fetched
  if (workflowState.isLoading) {
    return <div>Loading task workflow...</div>;
  }

  // Show error state if there was an error
  if (workflowState.error) {
    return <div>Error: {workflowState.error}</div>;
  }

  return (
    <SpaceBetween size="m">
      <TaskHeader taskId={taskId} />

      <Container>
        <SpaceBetween size="l">
          <TaskDetails
            taskId={taskId}
            items={associatedItems}
            onEditTransformations={handleEditTransformations}
          />

          <WorkflowProgress
            taskId={taskId}
            steps={workflowState.steps}
            activeStepIndex={workflowState.activeStepIndex}
            onStepChange={handleStepChange}
            onComplete={handleWorkflowComplete}
          />
        </SpaceBetween>
      </Container>
    </SpaceBetween>
  );
}
