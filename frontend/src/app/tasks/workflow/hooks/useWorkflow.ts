import { useState, useEffect } from 'react';
import { WorkflowStep, TaskDetails } from '../types';
import { getWorkflowConfig } from '../config/workflowConfig';

// Mock function to fetch task details - in a real app, this would be an API call
const fetchTaskDetails = async (taskId: string): Promise<TaskDetails> => {
  // This is a mock implementation - replace with actual API call
  return {
    id: taskId,
    name: `Task ${taskId}`,
    status: 'Pending',
    items: [
      { id: '1', name: 'Item 1', status: 'Pending' },
      { id: '2', name: 'Item 2', status: 'Migrated' },
      { id: '3', name: 'Item 3', status: 'Error' },
    ],
    transformationsCount: 3,
    workflowType: 'standard',
    currentStep: 0,
  };
};

export interface WorkflowState {
  taskDetails: TaskDetails | null;
  steps: WorkflowStep[];
  activeStepIndex: number;
  isLoading: boolean;
  error: string | null;
}

export interface WorkflowActions {
  goToStep: (stepIndex: number) => void;
  completeCurrentStep: () => void;
  updateStepData: (stepId: string, data: any) => void;
  completeWorkflow: () => void;
}

export function useWorkflow(taskId: string): [WorkflowState, WorkflowActions] {
  const [state, setState] = useState<WorkflowState>({
    taskDetails: null,
    steps: [],
    activeStepIndex: 0,
    isLoading: true,
    error: null,
  });

  // Load task details and initialize workflow
  useEffect(() => {
    const loadTaskDetails = async () => {
      try {
        setState(prev => ({ ...prev, isLoading: true, error: null }));
        
        const taskDetails = await fetchTaskDetails(taskId);
        const workflowConfig = getWorkflowConfig(taskDetails.workflowType);
        
        // Initialize steps with completion status based on current step
        const steps = workflowConfig.steps.map((step, index) => ({
          ...step,
          isCompleted: index < taskDetails.currentStep,
        }));

        setState({
          taskDetails,
          steps,
          activeStepIndex: taskDetails.currentStep,
          isLoading: false,
          error: null,
        });
      } catch (error) {
        setState(prev => ({
          ...prev,
          isLoading: false,
          error: error instanceof Error ? error.message : 'Failed to load task details',
        }));
      }
    };

    loadTaskDetails();
  }, [taskId]);

  // Actions for manipulating workflow state
  const actions: WorkflowActions = {
    goToStep: (stepIndex: number) => {
      if (stepIndex >= 0 && stepIndex < state.steps.length) {
        setState(prev => ({ ...prev, activeStepIndex: stepIndex }));
      }
    },

    completeCurrentStep: () => {
      const { activeStepIndex, steps } = state;
      
      if (activeStepIndex < steps.length) {
        // Mark current step as completed
        const updatedSteps = [...steps];
        updatedSteps[activeStepIndex] = {
          ...updatedSteps[activeStepIndex],
          isCompleted: true,
        };

        // Move to next step if available
        const nextStepIndex = activeStepIndex + 1;
        
        setState(prev => ({
          ...prev,
          steps: updatedSteps,
          activeStepIndex: nextStepIndex < steps.length ? nextStepIndex : activeStepIndex,
        }));

        // In a real app, you would save this progress to the backend
        // saveWorkflowProgress(taskId, nextStepIndex);
      }
    },

    updateStepData: (stepId: string, data: any) => {
      // In a real app, you would save this step data to the backend
      console.log(`Updating step ${stepId} with data:`, data);
    },

    completeWorkflow: () => {
      // Mark all steps as completed
      const updatedSteps = state.steps.map(step => ({
        ...step,
        isCompleted: true,
      }));

      setState(prev => ({
        ...prev,
        steps: updatedSteps,
      }));

      // In a real app, you would save this completion status to the backend
      // completeTaskWorkflow(taskId);
    },
  };

  return [state, actions];
}
