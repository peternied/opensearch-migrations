package org.opensearch.migrations.testutils;

import java.net.InetSocketAddress;
import java.net.URI;
import java.net.URISyntaxException;
import java.util.concurrent.atomic.AtomicReference;
import java.util.function.Function;

import com.sun.net.httpserver.HttpServer;
import com.sun.net.httpserver.HttpsConfigurator;
import com.sun.net.httpserver.HttpsParameters;
import com.sun.net.httpserver.HttpsServer;
import lombok.Lombok;

/**
 * This class brings up an HTTP(s) server with its constructor that returns responses
 * based upon a simple Function that is passed to the constructor.  This class can support
 * TLS, but only with an auto-generated self-signed cert.
 */
public class SimpleHttpServer implements AutoCloseable {

    public static final String LOCALHOST = "localhost";
    public static final int SOCKET_BACKLOG_SIZE = 10;
    protected final HttpServer httpServer;
    public final boolean useTls;

    public static SimpleHttpServer makeServer(
        boolean useTls,
        Function<HttpRequestFirstLine, SimpleHttpResponse> makeContext
    ) throws PortFinder.ExceededMaxPortAssigmentAttemptException {
        var testServerRef = new AtomicReference<SimpleHttpServer>();
        PortFinder.retryWithNewPortUntilNoThrow(port -> {
            try {
                testServerRef.set(new SimpleHttpServer(useTls, port, makeContext));
            } catch (Exception e) {
                throw Lombok.sneakyThrow(e);
            }
        });
        return testServerRef.get();
    }

    public static class PojoHttpRequestFirstLine implements HttpRequestFirstLine {
        private final String verb;
        private final URI path;
        private final String version;

        public PojoHttpRequestFirstLine(String verb, URI path, String version) {
            this.verb = verb;
            this.path = path;
            this.version = version;
        }

        @Override
        public String verb() {
            return verb;
        }

        @Override
        public URI path() {
            return path;
        }

        @Override
        public String version() {
            return version;
        }
    }

    private static HttpsServer createSecureServer(InetSocketAddress address) throws Exception {
        var httpsServer = HttpsServer.create(address, SOCKET_BACKLOG_SIZE);
        var sslContext = SelfSignedSSLContextBuilder.getSSLContext();
        httpsServer.setHttpsConfigurator(new HttpsConfigurator(sslContext) {
            public void configure(HttpsParameters params) {
                try {
                    params.setNeedClientAuth(false);
                    var engine = sslContext.createSSLEngine();
                    params.setCipherSuites(engine.getEnabledCipherSuites());
                    params.setProtocols(engine.getEnabledProtocols());

                    var defaultSSLParameters = sslContext.getDefaultSSLParameters();
                    params.setSSLParameters(defaultSSLParameters);
                } catch (Exception ex) {
                    ex.printStackTrace();
                    System.out.println("Failed to create HTTPS port");
                }
            }
        });

        return httpsServer;
    }

    /**
     * @param port
     * @return the port upon successfully binding the server
     */
    public SimpleHttpServer(boolean useTls, int port, Function<HttpRequestFirstLine, SimpleHttpResponse> contentMapper)
        throws Exception
    {
        var addr = new InetSocketAddress(LOCALHOST, port);
        this.useTls = useTls;
        httpServer = useTls ? createSecureServer(addr) : HttpServer.create(addr, 0);
        httpServer.createContext("/", httpExchange -> {
            var requestToMatch = new PojoHttpRequestFirstLine(
                httpExchange.getRequestMethod(),
                httpExchange.getRequestURI(),
                httpExchange.getProtocol()
            );
            var headersAndPayload = contentMapper.apply(requestToMatch);
            var responseHeaders = httpExchange.getResponseHeaders();
            for (var kvp : headersAndPayload.headers.entrySet()) {
                responseHeaders.set(kvp.getKey(), kvp.getValue());
            }

            httpExchange.sendResponseHeaders(headersAndPayload.statusCode, 0);
            var payload = headersAndPayload.payloadBytes;
            if (payload != null) {
                httpExchange.getResponseBody().write(headersAndPayload.payloadBytes);
                httpExchange.getResponseBody().flush();
            }
            httpExchange.getResponseBody().close();
            httpExchange.close();
        });
        httpServer.start();
    }

    public int port() {
        return httpServer.getAddress().getPort();
    }

    public URI localhostEndpoint() {
        try {
            return new URI((useTls ? "https" : "http"), null, LOCALHOST, port(), "/", null, null);
        } catch (URISyntaxException e) {
            throw new IllegalArgumentException("Error building URI", e);
        }
    }

    @Override
    public void close() {
        httpServer.stop(0);
    }
}
