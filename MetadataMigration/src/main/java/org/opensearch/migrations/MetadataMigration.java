package org.opensearch.migrations;

import java.util.Optional;

import org.opensearch.migrations.commands.Configure;
import org.opensearch.migrations.commands.Evaluate;
import org.opensearch.migrations.commands.EvaluateArgs;
import org.opensearch.migrations.commands.Migrate;
import org.opensearch.migrations.commands.MigrateArgs;
import org.opensearch.migrations.commands.Result;
import org.opensearch.migrations.metadata.tracing.RootMetadataMigrationContext;
import org.opensearch.migrations.tracing.ActiveContextTracker;
import org.opensearch.migrations.tracing.ActiveContextTrackerByActivityType;
import org.opensearch.migrations.tracing.CompositeContextTracker;
import org.opensearch.migrations.tracing.RootOtelContext;
import org.opensearch.migrations.utils.ProcessHelpers;

import com.beust.jcommander.JCommander;
import lombok.extern.slf4j.Slf4j;

@Slf4j
public class MetadataMigration {

    public static void main(String[] args) throws Exception {
        var arguments = new MetadataArgs();
        var migrateArgs = new MigrateArgs();
        var evaluateArgs = new EvaluateArgs(); 
        var jCommander = JCommander.newBuilder()
            .addObject(arguments)
            .addCommand(migrateArgs)
            .addCommand(evaluateArgs)
            .build();
        jCommander.parse(args);

        var context = new RootMetadataMigrationContext(
            RootOtelContext.initializeOpenTelemetryWithCollectorOrAsNoop(arguments.otelCollectorEndpoint, "metadata",
                ProcessHelpers.getNodeInstanceName()),
            new CompositeContextTracker(new ActiveContextTracker(), new ActiveContextTrackerByActivityType())
        );

        var meta = new MetadataMigration(arguments);

        log.atInfo().setMessage("Command line arguments: {}").addArgument(String.join(" ", args)).log();

        if (arguments.help || jCommander.getParsedCommand() == null) {
            jCommander.usage();
            return;
        }

        var command = Optional.ofNullable(jCommander.getParsedCommand())
            .map(cmd -> Enum.valueOf(MetadataCommands.class, cmd))
            .orElse(MetadataCommands.Migrate);
        Result result;
        switch (command) {
            default:
            case Migrate:
                log.info("Starting Metadata Migration");
                result = meta.migrate().execute(context);
                break;
            case Evaluate:
                log.info("Starting Metadata Evaluation");
                result = meta.evaluate().execute(context);
                break;
        }
        log.info(result.toString());
        System.exit(result.getExitCode());
    }

    private final MetadataArgs arguments;

    public MetadataMigration(MetadataArgs arguments) {
        this.arguments = arguments;
    }

    public Configure configure() {
        return new Configure();
    }

    public Evaluate evaluate() {
        return new Evaluate(arguments);
    }

    public Migrate migrate() {
        return new Migrate(arguments);
    }
}
