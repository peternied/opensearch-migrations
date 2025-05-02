# Workflow Module Architecture

This module implements a flexible and extensible workflow system for task management. It allows for different types of workflows with customizable steps and step-specific UI components.

## Directory Structure

```
workflow/
├── components/           # UI components
│   ├── steps/            # Step-specific components
│   │   ├── MetadataMigrationStep.tsx
│   │   └── index.ts
│   ├── TaskHeader.tsx
│   ├── TaskDetails.tsx
│   ├── TransformationsPanel.tsx
│   ├── WorkflowProgress.tsx
│   ├── StepRenderer.tsx
│   └── index.ts
├── config/               # Configuration
│   └── workflowConfig.ts # Workflow definitions
├── hooks/                # Custom React hooks
│   └── useWorkflow.ts    # Workflow state management
├── types/                # TypeScript type definitions
│   └── index.ts
├── page.tsx              # Main page component
└── README.md             # This file
```

## Key Concepts

### Workflow Configuration

Workflows are defined in `config/workflowConfig.ts`. Each workflow has a type and a list of steps. This allows for different workflow types (e.g., standard, lite) with different steps.

```typescript
// Example of adding a new workflow type
export const CUSTOM_WORKFLOW: WorkflowConfig = {
  type: 'custom',
  steps: [
    {
      id: 'custom-step-1',
      title: 'Custom Step 1',
      description: 'Description of custom step 1.'
    }
    // Add more steps as needed
  ]
};

// Add it to the workflow configs
export const WORKFLOW_CONFIGS: Record<string, WorkflowConfig> = {
  standard: STANDARD_WORKFLOW,
  lite: LITE_WORKFLOW,
  custom: CUSTOM_WORKFLOW
};
```

### Step Components

Each workflow step can have a custom UI component. Step components are defined in the `components/steps` directory and registered in the `StepRenderer` component.

To add a new step component:

1. Create a new component in `components/steps/`
2. Export it from `components/steps/index.ts`
3. Register it in `StepRenderer.tsx`

```typescript
// In StepRenderer.tsx
const STEP_COMPONENTS: Record<
  string,
  React.ComponentType<WorkflowStepComponentProps>
> = {
  'metadata-migration': MetadataMigrationStep,
  'custom-step-1': CustomStep1Component
  // Add more step components as they are created
};
```

### Workflow State Management

The `useWorkflow` hook manages the workflow state, including:

- Loading task details
- Tracking the active step
- Handling step transitions
- Storing step-specific data

## Extending the Workflow System

### Adding a New Workflow Type

1. Define a new workflow configuration in `config/workflowConfig.ts`
2. Add it to the `WORKFLOW_CONFIGS` object
3. The system will automatically use the new workflow type when specified in the task details

### Adding a New Step Component

1. Create a new component in `components/steps/` that implements the `WorkflowStepComponentProps` interface
2. Export it from `components/steps/index.ts`
3. Register it in the `STEP_COMPONENTS` map in `StepRenderer.tsx`

### Customizing Step Behavior

Each step component can:

- Implement custom validation logic
- Store and manage step-specific state
- Perform step-specific actions
- Render custom UI elements

## Usage Example

```typescript
// In a component that needs to use the workflow
import { useWorkflow } from './hooks/useWorkflow';

function MyComponent({ taskId }) {
  const [workflowState, workflowActions] = useWorkflow(taskId);

  // Use workflowState to access the current state
  const { steps, activeStepIndex } = workflowState;

  // Use workflowActions to manipulate the workflow
  const handleComplete = () => {
    workflowActions.completeCurrentStep();
  };

  // Render workflow components
  return (
    <div>
      <WorkflowProgress
        steps={steps}
        activeStepIndex={activeStepIndex}
        onStepChange={workflowActions.goToStep}
        onComplete={workflowActions.completeWorkflow}
      />
    </div>
  );
}
```
