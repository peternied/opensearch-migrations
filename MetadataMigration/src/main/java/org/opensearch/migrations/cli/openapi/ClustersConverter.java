package org.opensearch.migrations.cli.openapi;

import org.opensearch.migrations.bulkload.common.FileSystemRepo;
import org.opensearch.migrations.bulkload.common.S3Repo;
import org.opensearch.migrations.bulkload.common.http.ConnectionContext;
import org.opensearch.migrations.cli.Clusters;
import org.opensearch.migrations.cluster.ClusterReader;
import org.opensearch.migrations.cluster.ClusterSnapshotReader;
import org.opensearch.migrations.cluster.ClusterWriter;
import org.opensearch.migrations.cluster.RemoteCluster;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import lombok.extern.slf4j.Slf4j;

import java.util.HashMap;
import java.util.Map;

/**
 * Utility class to convert Clusters objects to OpenAPI-compatible JSON.
 * This creates JSON structures that match the OpenAPI-generated model format
 * without depending on the generated classes (which have missing dependencies).
 * Follows the established pattern from OpenApiConverter.java for consistency.
 */
@Slf4j
public class ClustersConverter {
    
    private static final ObjectMapper objectMapper = new ObjectMapper();

    /**
     * Converts a Clusters object to its OpenAPI-compatible JSON representation.
     * 
     * @param clusters The Clusters object to convert
     * @return JSON string representation matching OpenAPI model structure
     */
    public static String clustersToOpenApiJson(Clusters clusters) {
        try {
            Map<String, Object> clustersInfo = new HashMap<>();
            
            if (clusters.getSource() != null) {
                clustersInfo.put("source", clusterReaderToMap(clusters.getSource()));
            }
            
            if (clusters.getTarget() != null) {
                clustersInfo.put("target", clusterWriterToMap(clusters.getTarget()));
            }
            
            return objectMapper.writeValueAsString(clustersInfo);
        } catch (Exception e) {
            log.error("Error converting Clusters to OpenAPI JSON", e);
            // Fallback to original JSON if conversion fails
            return clusters.asJsonOutput().toString();
        }
    }

    /**
     * Converts a ClusterReader to a Map structure matching ClusterInfo model.
     * 
     * @param reader The ClusterReader to convert
     * @return Map with extracted data matching ClusterInfo structure
     */
    private static Map<String, Object> clusterReaderToMap(ClusterReader reader) {
        Map<String, Object> info = new HashMap<>();
        info.put("type", reader.getFriendlyTypeName());
        info.put("version", reader.getVersion().toString());

        // Handle ClusterSnapshotReader - extract repository information
        if (reader instanceof ClusterSnapshotReader) {
            var snapshotReader = (ClusterSnapshotReader) reader;
            var sourceRepo = snapshotReader.getSourceRepo();
            
            if (sourceRepo instanceof S3Repo) {
                var s3Repo = (S3Repo) sourceRepo;
                info.put("uri", s3Repo.getS3RepoUri().uri);
            } else if (sourceRepo instanceof FileSystemRepo) {
                info.put("localRepository", sourceRepo.getRepoRootDir().toString());
            }
        }

        // Handle RemoteCluster - extract connection details
        if (reader instanceof RemoteCluster) {
            var remoteCluster = (RemoteCluster) reader;
            extractConnectionDetails(info, remoteCluster.getConnection());
        }

        return info;
    }

    /**
     * Converts a ClusterWriter to a Map structure matching ClusterInfo model.
     * 
     * @param writer The ClusterWriter to convert
     * @return Map with extracted data matching ClusterInfo structure
     */
    private static Map<String, Object> clusterWriterToMap(ClusterWriter writer) {
        Map<String, Object> info = new HashMap<>();
        info.put("type", writer.getFriendlyTypeName());
        info.put("version", writer.getVersion().toString());

        // Handle RemoteCluster - extract connection details
        if (writer instanceof RemoteCluster) {
            var remoteCluster = (RemoteCluster) writer;
            extractConnectionDetails(info, remoteCluster.getConnection());
        }

        return info;
    }

    /**
     * Extracts connection details from ConnectionContext and maps them to ClusterInfo fields.
     * 
     * @param info The Map to populate with connection details
     * @param connection The ConnectionContext to extract from
     */
    private static void extractConnectionDetails(Map<String, Object> info, ConnectionContext connection) {
        var connectionData = connection.toUserFacingData();
        
        // Map known connection fields to ClusterInfo fields
        connectionData.forEach((key, value) -> {
            String lowerKey = key.toLowerCase();
            switch (lowerKey) {
                case "uri":
                case "endpoint":
                case "url":
                    info.put("uri", String.valueOf(value));
                    break;
                case "protocol":
                    info.put("protocol", String.valueOf(value));
                    break;
                case "insecure":
                    info.put("insecure", parseBoolean(value));
                    break;
                case "awsspecificauthentication":
                case "aws_specific_authentication":
                case "awsauth":
                    info.put("awsSpecificAuthentication", parseBoolean(value));
                    break;
                case "disablecompression":
                case "disable_compression":
                    info.put("disableCompression", parseBoolean(value));
                    break;
                case "compression":
                    // Invert compression to get disableCompression
                    info.put("disableCompression", !parseBoolean(value));
                    break;
                default:
                    // For unknown fields, we could log them or handle them differently
                    log.debug("Unknown connection field: {} = {}", key, value);
                    break;
            }
        });
    }
    
    /**
     * Helper method to safely parse boolean values from various types.
     * 
     * @param value The value to parse as boolean
     * @return Boolean value
     */
    private static Boolean parseBoolean(Object value) {
        if (value instanceof Boolean) {
            return (Boolean) value;
        } else if (value != null) {
            return Boolean.parseBoolean(String.valueOf(value));
        }
        return null;
    }
}
