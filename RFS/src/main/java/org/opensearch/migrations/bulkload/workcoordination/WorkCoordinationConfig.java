package org.opensearch.migrations.bulkload.workcoordination;

/**
 * Configuration for work coordination backend selection.
 */
public class WorkCoordinationConfig {
    
    public enum Backend {
        OPENSEARCH("opensearch"),
        CONSOLE("console");
        
        private final String value;
        
        Backend(String value) {
            this.value = value;
        }
        
        public String getValue() {
            return value;
        }
        
        public static Backend fromString(String value) {
            for (Backend backend : Backend.values()) {
                if (backend.value.equalsIgnoreCase(value)) {
                    return backend;
                }
            }
            throw new IllegalArgumentException("Unknown backend: " + value);
        }
    }
    
    private final Backend backend;
    private final String consoleApiBaseUrl;
    private final String sessionName;
    private final String workerId;
    
    // OpenSearch-specific fields
    private final AbstractedHttpClient openSearchHttpClient;
    private final long tolerableClientServerClockDifferenceSeconds;
    
    /**
     * Constructor for console-based coordination.
     */
    public WorkCoordinationConfig(Backend backend, String consoleApiBaseUrl, String sessionName, String workerId) {
        this.backend = backend;
        this.consoleApiBaseUrl = consoleApiBaseUrl;
        this.sessionName = sessionName;
        this.workerId = workerId;
        this.openSearchHttpClient = null;
        this.tolerableClientServerClockDifferenceSeconds = 0;
    }
    
    /**
     * Constructor for OpenSearch-based coordination.
     */
    public WorkCoordinationConfig(Backend backend, AbstractedHttpClient openSearchHttpClient, 
                                 long tolerableClientServerClockDifferenceSeconds, String workerId) {
        this.backend = backend;
        this.openSearchHttpClient = openSearchHttpClient;
        this.tolerableClientServerClockDifferenceSeconds = tolerableClientServerClockDifferenceSeconds;
        this.workerId = workerId;
        this.consoleApiBaseUrl = null;
        this.sessionName = null;
    }
    
    public Backend getBackend() {
        return backend;
    }
    
    public String getConsoleApiBaseUrl() {
        return consoleApiBaseUrl;
    }
    
    public String getSessionName() {
        return sessionName;
    }
    
    public String getWorkerId() {
        return workerId;
    }
    
    public AbstractedHttpClient getOpenSearchHttpClient() {
        return openSearchHttpClient;
    }
    
    public long getTolerableClientServerClockDifferenceSeconds() {
        return tolerableClientServerClockDifferenceSeconds;
    }
}
