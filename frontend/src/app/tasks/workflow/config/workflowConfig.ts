import { WorkflowConfig } from '../types';

// Standard workflow configuration
export const STANDARD_WORKFLOW: WorkflowConfig = {
  type: 'standard',
  steps: [
    {
      id: 'metadata-migration',
      title: 'Metadata Migration',
      description: 'Migrate task metadata to new format.'
    },
    {
      id: 'percentage-backfill',
      title: '% Backfill',
      description: 'Perform a tiny backfill to test data migration.'
    },
    {
      id: 'full-backfill',
      title: 'Full Backfill',
      description: 'Backfill all data into the new system.'
    },
    {
      id: 'percentage-replay',
      title: '% Replay',
      description: 'Replay a tiny percentage of production traffic.'
    },
    {
      id: 'full-replay',
      title: 'Full Replay',
      description: 'Replay all related production traffic.'
    }
  ]
};

// Lite workflow with fewer steps
export const LITE_WORKFLOW: WorkflowConfig = {
  type: 'lite',
  steps: [
    {
      id: 'metadata-migration',
      title: 'Metadata Migration',
      description: 'Migrate task metadata to new format.'
    },
    {
      id: 'full-backfill',
      title: 'Full Backfill',
      description: 'Backfill all data into the new system.'
    },
    {
      id: 'full-replay',
      title: 'Full Replay',
      description: 'Replay all related production traffic.'
    }
  ]
};

// Map of all available workflow configurations
export const WORKFLOW_CONFIGS: Record<string, WorkflowConfig> = {
  standard: STANDARD_WORKFLOW,
  lite: LITE_WORKFLOW
};

// Default workflow type
export const DEFAULT_WORKFLOW_TYPE = 'standard';

// Get workflow configuration by type
export function getWorkflowConfig(
  type: string = DEFAULT_WORKFLOW_TYPE
): WorkflowConfig {
  return WORKFLOW_CONFIGS[type] || STANDARD_WORKFLOW;
}
