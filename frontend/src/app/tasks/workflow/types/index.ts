import { ReactNode } from 'react';

// Task related types
export interface TaskItem {
  id: string;
  name: string;
  status: string;
}

// Workflow step types
export interface WorkflowStep {
  id: string;
  title: string;
  description: string;
  isCompleted?: boolean;
  isOptional?: boolean;
  validationRules?: ValidationRule[];
}

export interface WorkflowStepComponentProps {
  step: WorkflowStep;
  stepData: any;
  onUpdate: (data: any) => void;
  onComplete: () => void;
  isActive: boolean;
}

export interface ValidationRule {
  validate: (data: any) => boolean;
  errorMessage: string;
}

// Workflow configuration
export interface WorkflowConfig {
  steps: WorkflowStep[];
  type: string;
}

// Component props
export interface TaskHeaderProps {
  taskId: string;
}

export interface TaskDetailsProps {
  taskId: string;
  items: TaskItem[];
  onEditTransformations: () => void;
}

export interface WorkflowProgressProps {
  taskId: string;
  steps: WorkflowStep[];
  activeStepIndex: number;
  onStepChange: (stepIndex: number) => void;
  onComplete: () => void;
}

export interface TransformationsPanelProps {
  count: number;
  onEdit: () => void;
}

// Service response types
export interface TaskDetails {
  id: string;
  name: string;
  status: string;
  items: TaskItem[];
  transformationsCount: number;
  workflowType: string;
  currentStep: number;
}
