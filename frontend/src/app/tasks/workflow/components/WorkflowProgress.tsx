import Wizard from '@cloudscape-design/components/wizard';
import Box from '@cloudscape-design/components/box';
import Button from '@cloudscape-design/components/button';
import SpaceBetween from '@cloudscape-design/components/space-between';
import { useRouter } from 'next/navigation';
import { WorkflowProgressProps } from '../types';
import { StepRenderer } from './StepRenderer';
import { useState } from 'react';

export function WorkflowProgress({ 
  taskId, 
  steps, 
  activeStepIndex, 
  onStepChange, 
  onComplete 
}: WorkflowProgressProps) {
  const router = useRouter();
  // Store step data for each step
  const [stepsData, setStepsData] = useState<Record<string, any>>({});

  const handleNavigateToTasks = () => {
    router.push('/tasks/manage');
  };

  const handleIgnoreTask = () => {
    if (confirm('Are you sure you want to ignore this task?')) {
      router.push('/tasks/manage');
    }
  };

  const handleStepDataUpdate = (stepId: string, data: any) => {
    setStepsData(prev => ({
      ...prev,
      [stepId]: data
    }));
  };

  const handleStepComplete = () => {
    // Move to the next step
    if (activeStepIndex < steps.length - 1) {
      onStepChange(activeStepIndex + 1);
    } else {
      // If this is the last step, complete the workflow
      onComplete();
    }
  };

  // Convert steps to wizard format
  const wizardSteps = steps.map(step => ({
    title: step.title,
    info: step.description,
    content: (
      <StepRenderer
        step={step}
        stepData={stepsData[step.id]}
        onUpdate={(data) => handleStepDataUpdate(step.id, data)}
        onComplete={handleStepComplete}
        isActive={steps.indexOf(step) === activeStepIndex}
      />
    ),
    isOptional: step.isOptional,
  }));

  return (
    <>
      <Box variant="h2">Workflow Progress</Box>
      <Wizard
        i18nStrings={{
          stepNumberLabel: stepNumber => `Step ${stepNumber}`,
          collapsedStepsLabel: (stepNumber, stepsCount) => `Step ${stepNumber} of ${stepsCount}`,
          cancelButton: '',
          previousButton: 'Previous',
          nextButton: 'Next',
          submitButton: 'Finish',
        }}
        activeStepIndex={activeStepIndex}
        onNavigate={({ detail }) => onStepChange(detail.requestedStepIndex)}
        allowSkipTo={true}
        secondaryActions={
          <SpaceBetween size="m" direction="horizontal">
            <Button onClick={handleNavigateToTasks}>Back to Tasks</Button>
            <Button onClick={handleIgnoreTask}>Ignore this task</Button>
          </SpaceBetween>
        }
        steps={wizardSteps}
        onSubmit={onComplete}
      />
    </>
  );
}
