package com.rfs.version_universal;

import java.util.Map;

import com.rfs.common.http.ConnectionContext;

public class RemoteReaderClient_ES_6_8 extends RemoteReaderClient {

    public RemoteReaderClient_ES_6_8(ConnectionContext connection) {
        super(connection);
    }

    @Override
    protected Map<String, String> getTemplateEndpoints() {
        return Map.of(
            "templates", "_template"
        );
    }
}
