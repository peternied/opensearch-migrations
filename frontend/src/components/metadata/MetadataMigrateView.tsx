"use client";

import { SessionStatusProps } from "../session/types";
import StatusContainer from "../session/StatusContainer";
import { MetadataDebugControls } from "./debug/MetadataDebugControls";
import { useMetadataMigrateAction } from "@/hooks/apiAction";
import { Alert, Box, Button, SpaceBetween, Table, TableProps, TextFilter } from "@cloudscape-design/components";
import { ItemResult, MetadataClusterInfo } from "@/generated/api";
import { useCollection } from '@cloudscape-design/collection-hooks';
import { useMemo, useState } from "react";

interface MetadataMigrateViewProps extends SessionStatusProps {
    readonly dryRun: boolean;
}

export default function MetadataMigrateView({
  sessionName,
  dryRun
}: MetadataMigrateViewProps) {
    const {
        run: runMetadataAction,
        data,
        reset,
        isLoading,
        error,
    } = useMetadataMigrateAction(dryRun);

    const triggerMetadataAction = async () => {
      reset();
      await runMetadataAction(sessionName);
    };

    type ItemKind = "Index" | "Alias" | "Index Template" | "Component Template";
    type ItemResultWithType = ItemResult & { type: ItemKind };

    function withType<T extends ItemResult>(items: T[] | undefined, type: ItemKind): ItemResultWithType[] {
      return (items ?? []).map(item => ({ ...item, type }));
    }

    const metadataItems = useMemo(() => {
      return [
        ...withType(data?.items?.aliases, "Alias"),
        ...withType(data?.items?.indexes, "Index"),
        ...withType(data?.items?.indexTemplates, "Index Template"),
        ...withType(data?.items?.componentTemplates, "Component Template"),
      ];
    }, [data]);

    const columnDefinitions: TableProps.ColumnDefinition<ItemResultWithType>[] = [
    {
      id: 'name', 
      header: 'Index name', 
      cell: (item) => item.name, 
      sortingField: "name"
    },
    {
      id: 'type',
      header: 'Type',
      cell: (item) => item.type,
      sortingField: "type"
    },
    {
      id: 'result',
      header: 'Success',
      cell: (item) => item.successful,
      sortingField: "successful"
    },
    {
      id: 'error-type',
      header: 'Error Type',
      cell: (item) => item.failure?.type ?? "",
      sortingField: "failure?.type"
    },
    {
      id: 'error-details',
      header: 'Error Type',
      cell: (item) => item.failure?.message ?? "",
      sortingField: "failure?.message"
    }
  ];


  const metadataItemCollection = useCollection(metadataItems, {
    filtering: {
      empty: (
        <Box textAlign="center" color="inherit">
          <b>No items</b>
        </Box>
      ),
      noMatch: <Box>No items match the filter criteria.</Box>
    },
    sorting: {
      defaultState: {
        sortingColumn: {
          sortingField: "name"
        }
      } 
    }
  });

  const maxHeight = "300px";
  return (
    <SpaceBetween size="l">

      {error && (
        <Alert type="error" header="Error">
          {String(error)}
        </Alert>
      )}

      <Button
        onClick={triggerMetadataAction}
        loading={isLoading}
        disabled={isLoading}
      >Run Metadata {dryRun ? "Evaluation" : "Migration"}</Button>

      <div style={{ maxHeight, overflow: 'auto' }}>
        <Table<ItemResultWithType>
          {...metadataItemCollection.collectionProps}
          columnDefinitions={columnDefinitions}
          items={metadataItemCollection.items}
          empty={
            <Box textAlign="center" color="inherit">
              <b>No items</b>
            </Box>
          }
          loading={isLoading}
          filter={
            <TextFilter
              {...metadataItemCollection.filterProps}
              filteringPlaceholder="Find an item"
            />
          }
          variant="borderless"
          stickyHeader
        />
      </div>
    </SpaceBetween>
  );
}
