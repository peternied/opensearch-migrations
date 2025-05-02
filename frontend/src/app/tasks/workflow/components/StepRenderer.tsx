import { WorkflowStep, WorkflowStepComponentProps } from '../types';
import { MetadataMigrationStep } from './steps';

// Default step component for steps that don't have a specific implementation
function DefaultStepComponent({ step, isActive }: WorkflowStepComponentProps) {
  if (!isActive) return null;

  return (
    <div>
      <h3>{step.title}</h3>
      <p>{step.description}</p>
      <p>TDB...</p>
    </div>
  );
}

// Map of step IDs to their corresponding components
const STEP_COMPONENTS: Record<
  string,
  React.ComponentType<WorkflowStepComponentProps>
> = {
  'metadata-migration': MetadataMigrationStep
  // Add more step components as they are created
  // 'percentage-backfill': PercentageBackfillStep,
  // 'full-backfill': FullBackfillStep,
  // 'percentage-replay': PercentageReplayStep,
  // 'full-replay': FullReplayStep,
};

interface StepRendererProps {
  step: WorkflowStep;
  stepData: unknown;
  onUpdate: (data: unknown) => void;
  onComplete: () => void;
  isActive: boolean;
}

export function StepRenderer({
  step,
  stepData,
  onUpdate,
  onComplete,
  isActive
}: StepRendererProps) {
  // Get the component for this step, or use the default if none exists
  const StepComponent = STEP_COMPONENTS[step.id] || DefaultStepComponent;

  return (
    <StepComponent
      step={step}
      stepData={stepData}
      onUpdate={onUpdate}
      onComplete={onComplete}
      isActive={isActive}
    />
  );
}
