import { useState } from 'react';
import SpaceBetween from '@cloudscape-design/components/space-between';
import Button from '@cloudscape-design/components/button';
import FormField from '@cloudscape-design/components/form-field';
import Checkbox from '@cloudscape-design/components/checkbox';
import { WorkflowStepComponentProps } from '../../types';

export function MetadataMigrationStep({
  step,
  stepData,
  onUpdate,
  onComplete,
  isActive
}: WorkflowStepComponentProps) {
  const [migrationOptions, setMigrationOptions] = useState({
    preserveOriginalMetadata: stepData?.preserveOriginalMetadata || true,
    migratePermissions: stepData?.migratePermissions || true,
    migrateAliases: stepData?.migrateAliases || true,
  });

  const handleOptionChange = (option: string, checked: boolean) => {
    const updatedOptions = {
      ...migrationOptions,
      [option]: checked,
    };
    
    setMigrationOptions(updatedOptions);
    onUpdate(updatedOptions);
  };

  const handleStartMigration = () => {
    // In a real app, this would trigger the actual migration process
    console.log('Starting metadata migration with options:', migrationOptions);
    
    // Simulate a migration process
    setTimeout(() => {
      console.log('Metadata migration completed');
      onComplete();
    }, 1500);
  };

  if (!isActive) {
    return null;
  }

  return (
    <SpaceBetween size="l">
      <FormField label="Migration Options">
        <SpaceBetween size="s">
          <Checkbox
            checked={migrationOptions.preserveOriginalMetadata}
            onChange={({ detail }) => 
              handleOptionChange('preserveOriginalMetadata', detail.checked)
            }
          >
            Preserve original metadata
          </Checkbox>
          
          <Checkbox
            checked={migrationOptions.migratePermissions}
            onChange={({ detail }) => 
              handleOptionChange('migratePermissions', detail.checked)
            }
          >
            Migrate security permissions
          </Checkbox>
          
          <Checkbox
            checked={migrationOptions.migrateAliases}
            onChange={({ detail }) => 
              handleOptionChange('migrateAliases', detail.checked)
            }
          >
            Migrate index aliases
          </Checkbox>
        </SpaceBetween>
      </FormField>

      <Button variant="primary" onClick={handleStartMigration}>
        Start Metadata Migration
      </Button>
    </SpaceBetween>
  );
}
