package org.opensearch.migrations.cli;

import java.util.ArrayList;
import java.util.List;

import org.opensearch.migrations.clusters.RemoteCluster;
import org.opensearch.migrations.clusters.SourceCluster;

import lombok.extern.slf4j.Slf4j;
import org.slf4j.event.Level;

@Slf4j
public class Clusters implements Printable, Validate {
    private SourceCluster source;
    private RemoteCluster target;
    private List<Message> messages = new ArrayList<>();

    public Clusters() {
    }

    public void setSource(SourceCluster source) {
        this.source = source;
    }

    public void setTarget(RemoteCluster target) {
        this.target = target;
    }

    @Override
    public Printer asPrinter() {
       var printerBuilder = new Printer.Builder()
            .section("Clusters")
            .entry(source)
            .entry(target);

        if (messages != null && !messages.isEmpty()) {
            printerBuilder.messages(messages);
        }
        return printerBuilder.build();
    }

    @Override
    public boolean validate() {
        if (source == null) {
            messages.add(Message.Builder().level(Level.ERROR).body("No source cluster specified").build());
            return false;
        }
    
        if (target == null) {
            messages.add(Message.Builder().level(Level.WARN).body("No target cluster specified").build());
        }
        return true;
    }
}
