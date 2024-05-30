package com.rfs.tracing;

import static org.hamcrest.CoreMatchers.equalTo;
import static org.hamcrest.MatcherAssert.assertThat;


import org.junit.jupiter.api.Test;

import io.opentelemetry.api.OpenTelemetry;
import io.opentelemetry.api.baggage.propagation.W3CBaggagePropagator;
import io.opentelemetry.api.trace.propagation.W3CTraceContextPropagator;
import io.opentelemetry.context.propagation.ContextPropagators;
import io.opentelemetry.context.propagation.TextMapPropagator;
import io.opentelemetry.exporter.logging.LoggingMetricExporter;
import io.opentelemetry.exporter.logging.LoggingSpanExporter;
import io.opentelemetry.exporter.logging.SystemOutLogRecordExporter;
import io.opentelemetry.sdk.OpenTelemetrySdk;
import io.opentelemetry.sdk.logs.SdkLoggerProvider;
import io.opentelemetry.sdk.logs.export.BatchLogRecordProcessor;
import io.opentelemetry.sdk.metrics.SdkMeterProvider;
import io.opentelemetry.sdk.metrics.export.PeriodicMetricReader;
import io.opentelemetry.sdk.resources.Resource;
import io.opentelemetry.sdk.trace.SdkTracerProvider;
import io.opentelemetry.sdk.trace.export.SimpleSpanProcessor;
import io.opentelemetry.semconv.ResourceAttributes;

public class DebugContext {
    public static OpenTelemetry create() {
        // Initialize the resource with service attributes
        Resource resource = Resource.getDefault()
            .toBuilder()
            .put(ResourceAttributes.SERVICE_NAME, "rfs")
            .put(ResourceAttributes.SERVICE_VERSION, "0.1.0")
            .build();
        
        // Initialize the SDK Tracer Provider
        SdkTracerProvider sdkTracerProvider = SdkTracerProvider.builder()
            .addSpanProcessor(SimpleSpanProcessor.create(LoggingSpanExporter.create()))
            .setResource(resource)
            .build();
        
        // Initialize the SDK Meter Provider
        SdkMeterProvider sdkMeterProvider = SdkMeterProvider.builder()
            .registerMetricReader(PeriodicMetricReader.builder(LoggingMetricExporter.create()).build())
            .setResource(resource)
            .build();
        
        // Initialize the SDK Logger Provider
        SdkLoggerProvider sdkLoggerProvider = SdkLoggerProvider.builder()
            .addLogRecordProcessor(BatchLogRecordProcessor.builder(SystemOutLogRecordExporter.create()).build())
            .setResource(resource)
            .build();
        
        // Build and register the OpenTelemetry SDK
        OpenTelemetry openTelemetry = OpenTelemetrySdk.builder()
            .setTracerProvider(sdkTracerProvider)
            .setMeterProvider(sdkMeterProvider)
            .setLoggerProvider(sdkLoggerProvider)
            .setPropagators(ContextPropagators.create(TextMapPropagator.composite(W3CTraceContextPropagator.getInstance(), W3CBaggagePropagator.getInstance())))
            .buildAndRegisterGlobal();
        
        // Print confirmation to verify that OpenTelemetry has been initialized
        System.out.println("OpenTelemetry SDK initialized with DebugContext");
        
        return openTelemetry;
    }

    @Test
    public void mytest(){
        var context = TestContext.withConsoleDebugging();

        try (final var snapshotContext = context.createSnapshotCreateContext()) {
            snapshotContext.addEvent("helo");
            try (final var registerContext = snapshotContext.createRegisterRequest()) {
                registerContext.addEvent("registerd");
                registerContext.addBytesSent(33);
                registerContext.addBytesRead(23);
                registerContext.addBytesRead(23);
                System.out.println("done");
                assertThat("abc", equalTo("a" + "bc"));
            }
        }


    }
}
