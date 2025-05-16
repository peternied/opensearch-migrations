import { useState } from 'react';
import SpaceBetween from '@cloudscape-design/components/space-between';
import Button from '@cloudscape-design/components/button';
import FormField from '@cloudscape-design/components/form-field';
import Checkbox from '@cloudscape-design/components/checkbox';
import { WorkflowStepComponentProps } from '../../types';
import Input from '@cloudscape-design/components/input';

export function MetadataMigrationStep({
  stepData,
  onUpdate,
  onComplete,
  isActive
}: WorkflowStepComponentProps) {
  const [migrationOptions, setMigrationOptions] = useState({
    preserveOriginalMetadata: stepData?.preserveOriginalMetadata || true,
    migratePermissions: stepData?.migratePermissions || true,
    migrateAliases: stepData?.migrateAliases || true
  });

  const handleOptionChange = (option: string, checked: boolean) => {
    const updatedOptions = {
      ...migrationOptions,
      [option]: checked
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
      <FormField label="Select Migration Options" description='Determine which metadata options should be applied when the associated indexes (3) are migrated.'>
        <SpaceBetween size="m">
          <Checkbox
            checked={migrationOptions.migrateAliases}
            onChange={({ detail }) =>
              handleOptionChange('migrateAliases', detail.checked)
            }
          >
            Migrate index aliases
          </Checkbox>
          <Checkbox
            checked={migrationOptions.migrateAliases}
            onChange={({ detail }) =>
              handleOptionChange('migrateAliases', detail.checked)
            }
          >
            Apply (3) transformations
          </Checkbox>
          <Checkbox
            checked={migrationOptions.preserveOriginalMetadata}
            onChange={({ detail }) =>
              handleOptionChange('preserveOriginalMetadata', detail.checked)
            }
          >
            Union types into index with same name
          </Checkbox>

          <Checkbox
            checked={migrationOptions.migratePermissions}
            onChange={({ detail }) =>
              handleOptionChange('migratePermissions', detail.checked)
            }
          >
            Update shard count
            <Input inputMode="numeric" value={'5'}></Input>
          </Checkbox>
        </SpaceBetween>
      </FormField>

      <Button variant="primary" onClick={handleStartMigration}>
        Start Metadata Migration
      </Button>
    </SpaceBetween>
  );
}
