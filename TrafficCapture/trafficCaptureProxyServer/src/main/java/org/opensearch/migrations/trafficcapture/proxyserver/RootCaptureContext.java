package org.opensearch.migrations.trafficcapture.proxyserver;

import io.opentelemetry.api.OpenTelemetry;
import lombok.Getter;
import org.opensearch.migrations.trafficcapture.kafkaoffloader.tracing.IRootKafkaOffloaderContext;
import org.opensearch.migrations.trafficcapture.kafkaoffloader.tracing.KafkaRecordContext;
import org.opensearch.migrations.trafficcapture.netty.tracing.RootWireLoggingContext;
import org.opensearch.migrations.trafficcapture.netty.tracing.WireCaptureContexts;

public class RootCaptureContext extends RootWireLoggingContext implements IRootKafkaOffloaderContext {

    public static final String SCOPE_NAME = "captureProxy";
    @Getter
    public final KafkaRecordContext.MetricInstruments kafkaOffloadingInstruments;

    public RootCaptureContext(OpenTelemetry openTelemetry) {
        this(openTelemetry, SCOPE_NAME);
    }

    public RootCaptureContext(OpenTelemetry openTelemetry, String scopeName) {
        super(openTelemetry, scopeName);
        var meter = this.getMeterProvider().get(scopeName);
        kafkaOffloadingInstruments = KafkaRecordContext.makeMetrics(meter);
    }
}