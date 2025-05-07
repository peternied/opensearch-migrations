import { SessionWorkflow, workflowIcon } from "@/context/migration-session";
import { Box, FormField, Icon, Popover, SpaceBetween, Tiles } from "@cloudscape-design/components";
import { ReactNode, useState } from "react";

export type WorkflowOption = {
  value: SessionWorkflow;
  label: string;
  description: string;
};

const WORKFLOW_OPTIONS: WorkflowOption[] = [
    {
      value: 'backfill',
      label: 'Backfill',
      description:
        'Transfer existing historical data to the new system without impacting live traffic.'
    },
    {
      value: 'replay',
      label: 'Traffic Capture/Replay',
      description:
        'Capture live traffic and replay it in the new environment for testing and validation.'
    },
    {
      value: 'full',
      label: 'Combined Capture + Replay',
      description:
        'Perform backfill and then begin traffic capture and replay in a single workflow.'
    },
    {
      value: 'freeform',
      label: 'Freeform Exploration',
      description:
        'Explore the Migration Assistant website without committing to a specific workflow.'
    }
  ];

  interface WorkflowPickerProps {
    value: SessionWorkflow;
    onChange: (value: SessionWorkflow) => void;
  }
  function renderLabelWithIcon(
    option: WorkflowOption,
    isDisabled: boolean
  ): ReactNode {
    const labelContent = (
      <SpaceBetween size="xs" direction="horizontal">
        <Box padding={{ right: 'l' }}>
          <Icon name={workflowIcon(option.value)} size="big" />
        </Box>
        <span>{option.label}</span>
      </SpaceBetween>
    );
  
    if (!isDisabled) return labelContent;
  
    return (
      <Popover
        dismissAriaLabel="Close info"
        position="right"
        size="small"
        triggerType="custom"
        content={
          <span>
            This option is only available via the command line tool.
          </span>
        }
      >
        <Box>{labelContent}</Box>
      </Popover>
    );
  }
  
  export default function WorkflowPicker({ value, onChange }: WorkflowPickerProps) {
    return (
      <FormField label="Workflow Type" description="Choose the appropriate workflow.">
        <Tiles
          value={value}
          onChange={({ detail }) =>
            onChange(detail.value as SessionWorkflow)
          }
          items={WORKFLOW_OPTIONS.map((option) => {
            const isDisabled = option.value !== 'backfill';
            return {
              value: option.value,
              label: renderLabelWithIcon(option, isDisabled),
              disabled: isDisabled,
              description: option.description
            };
          })}
        />
      </FormField>
    );
  }