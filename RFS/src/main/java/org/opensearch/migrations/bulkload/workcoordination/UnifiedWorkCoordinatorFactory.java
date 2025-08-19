package org.opensearch.migrations.bulkload.workcoordination;

import org.opensearch.migrations.Version;
import org.opensearch.migrations.VersionMatchers;
import org.opensearch.migrations.bulkload.version_es_6_8.OpenSearchWorkCoordinator_ES_6_8;
import org.opensearch.migrations.bulkload.version_os_2_11.OpenSearchWorkCoordinator_OS_2_11;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.Clock;
import java.util.function.Consumer;

/**
 * Unified factory that can create either OpenSearch-based or console-based work coordinators
 * based on configuration.
 */
public class UnifiedWorkCoordinatorFactory {
    private static final Logger logger = LoggerFactory.getLogger(UnifiedWorkCoordinatorFactory.class);
    
    private final Version version;
    private final String indexNameSuffix;
    
    public UnifiedWorkCoordinatorFactory(Version version, String indexNameSuffix) {
        this.version = version;
        this.indexNameSuffix = indexNameSuffix != null ? indexNameSuffix : "";
    }
    
    public UnifiedWorkCoordinatorFactory(Version version) {
        this(version, "");
    }
    
    /**
     * Create a work coordinator based on the provided configuration.
     */
    public IWorkCoordinator create(WorkCoordinationConfig config) {
        switch (config.getBackend()) {
            case CONSOLE:
                logger.info("Creating ConsoleWorkCoordinator with baseUrl: {}, session: {}", 
                           config.getConsoleApiBaseUrl(), config.getSessionName());
                return new ConsoleWorkCoordinator(
                    config.getConsoleApiBaseUrl(),
                    config.getSessionName(),
                    config.getWorkerId()
                );
                
            case OPENSEARCH:
                logger.info("Creating OpenSearchWorkCoordinator for version: {}", version);
                return createOpenSearchCoordinator(
                    config.getOpenSearchHttpClient(),
                    config.getTolerableClientServerClockDifferenceSeconds(),
                    config.getWorkerId()
                );
                
            default:
                throw new IllegalArgumentException("Unknown backend: " + config.getBackend());
        }
    }
    
    /**
     * Create a work coordinator with custom clock and work item consumer.
     */
    public IWorkCoordinator create(WorkCoordinationConfig config, Clock clock, 
                                  Consumer<IWorkCoordinator.WorkItemAndDuration> workItemConsumer) {
        switch (config.getBackend()) {
            case CONSOLE:
                logger.info("Creating ConsoleWorkCoordinator with baseUrl: {}, session: {}", 
                           config.getConsoleApiBaseUrl(), config.getSessionName());
                // ConsoleWorkCoordinator doesn't support custom clock/consumer in the same way
                // For now, return the basic version
                return new ConsoleWorkCoordinator(
                    config.getConsoleApiBaseUrl(),
                    config.getSessionName(),
                    config.getWorkerId()
                );
                
            case OPENSEARCH:
                logger.info("Creating OpenSearchWorkCoordinator for version: {} with custom clock", version);
                return createOpenSearchCoordinator(
                    config.getOpenSearchHttpClient(),
                    config.getTolerableClientServerClockDifferenceSeconds(),
                    config.getWorkerId(),
                    clock,
                    workItemConsumer
                );
                
            default:
                throw new IllegalArgumentException("Unknown backend: " + config.getBackend());
        }
    }
    
    /**
     * Helper method to create OpenSearch coordinators based on version.
     */
    private OpenSearchWorkCoordinator createOpenSearchCoordinator(
            AbstractedHttpClient httpClient,
            long tolerableClientServerClockDifferenceSeconds,
            String workerId) {
        
        if (VersionMatchers.anyOS.or(VersionMatchers.isES_7_X).or(VersionMatchers.isES_8_X).test(version)) {
            return new OpenSearchWorkCoordinator_OS_2_11(httpClient,
                indexNameSuffix,
                tolerableClientServerClockDifferenceSeconds,
                workerId);
        } else if (VersionMatchers.isES_6_X.or(VersionMatchers.isES_5_X).test(version)) {
            return new OpenSearchWorkCoordinator_ES_6_8(httpClient,
                indexNameSuffix,
                tolerableClientServerClockDifferenceSeconds,
                workerId);
        } else {
            throw new IllegalArgumentException("Unsupported version: " + version);
        }
    }
    
    /**
     * Helper method to create OpenSearch coordinators with custom clock and consumer.
     */
    private OpenSearchWorkCoordinator createOpenSearchCoordinator(
            AbstractedHttpClient httpClient,
            long tolerableClientServerClockDifferenceSeconds,
            String workerId,
            Clock clock,
            Consumer<IWorkCoordinator.WorkItemAndDuration> workItemConsumer) {
        
        if (VersionMatchers.anyOS.or(VersionMatchers.isES_7_X).or(VersionMatchers.isES_8_X).test(version)) {
            return new OpenSearchWorkCoordinator_OS_2_11(httpClient,
                indexNameSuffix,
                tolerableClientServerClockDifferenceSeconds,
                workerId,
                clock,
                workItemConsumer);
        } else if (VersionMatchers.isES_6_X.or(VersionMatchers.isES_5_X).test(version)) {
            return new OpenSearchWorkCoordinator_ES_6_8(httpClient,
                indexNameSuffix,
                tolerableClientServerClockDifferenceSeconds,
                workerId,
                clock,
                workItemConsumer);
        } else {
            throw new IllegalArgumentException("Unsupported version: " + version);
        }
    }
    
    /**
     * Create configuration for console-based coordination.
     */
    public static WorkCoordinationConfig createConsoleConfig(String baseUrl, String sessionName, String workerId) {
        return new WorkCoordinationConfig(
            WorkCoordinationConfig.Backend.CONSOLE,
            baseUrl,
            sessionName,
            workerId
        );
    }
    
    /**
     * Create configuration for OpenSearch-based coordination.
     */
    public static WorkCoordinationConfig createOpenSearchConfig(AbstractedHttpClient httpClient,
                                                               long tolerableClockDifferenceSeconds,
                                                               String workerId) {
        return new WorkCoordinationConfig(
            WorkCoordinationConfig.Backend.OPENSEARCH,
            httpClient,
            tolerableClockDifferenceSeconds,
            workerId
        );
    }
    
    /**
     * Get the final index name that would be used for OpenSearch coordination.
     */
    public String getFinalIndexName() {
        return OpenSearchWorkCoordinator.getFinalIndexName(indexNameSuffix);
    }
}
