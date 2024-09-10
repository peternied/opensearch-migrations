package org.opensearch.migrations;

/** The list of supported commands for the metadata tool */
public enum MetadataCommands {
    /** Migrates items from a source and recreates them on the target cluster */
    Migrate,

    /** Inspects items from a source to determine which can be placed on a target cluster */
    Evaluate;
}
