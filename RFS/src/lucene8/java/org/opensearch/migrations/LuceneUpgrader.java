package org.opensearch.migrations;

public interface LuceneUpgrader {
    void upgradeIndex(String indexPath);
}
