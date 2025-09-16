package org.opensearch.migrations.bulkload.lucene.version_9;

import java.lang.reflect.Field;
import java.lang.reflect.InvocationHandler;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;
import java.util.Arrays;
import java.util.HashMap;
import java.util.Map;

import lombok.extern.slf4j.Slf4j;
import shadow.lucene9.org.apache.lucene.codecs.Codec;

/**
 * A registry that overrides Lucene's default codec loading mechanism to provide
 * dynamic fallback codecs for unknown codec types. This class uses reflection to
 * access and modify Lucene's internal codec registry.
 * 
 * This approach avoids the need to manually register a new fallback codec for each
 * unknown codec encountered by our application.
 */
@Slf4j
public class DynamicCodecRegistry {
    
    private static boolean initialized = false;
    private static final Object LOCK = new Object();
    private static final String LOADER_FIELD_NAME = "loader";
    private static final String LOOKUP_METHOD_NAME = "lookup";
    
    /**
     * Initializes the dynamic codec registry by patching Lucene's internal
     * codec loading mechanism.
     * 
     * @return true if initialization was successful, false otherwise
     */
    public static boolean initialize() {
        synchronized (LOCK) {
            if (initialized) {
                return true; // Already initialized
            }
            
            try {
                // Access the private static 'loader' field in Codec class
                Field loaderField = Codec.class.getDeclaredField(LOADER_FIELD_NAME);
                loaderField.setAccessible(true);
                
                // Get the current loader instance
                Object originalLoader = loaderField.get(null);
                
                // Create our custom loader wrapping the original one
                Object dynamicLoader = createDynamicLoaderProxy(originalLoader);
                
                // Replace the original loader with our custom one
                loaderField.set(null, dynamicLoader);
                
                // Initialize the lookup method to ensure our loader is used
                Method reloadMethod = Codec.class.getDeclaredMethod("reloadCodecs");
                reloadMethod.setAccessible(true);
                reloadMethod.invoke(null);
                
                log.info("Successfully initialized dynamic codec registry");
                initialized = true;
                return true;
                
            } catch (Exception e) {
                log.error("Failed to initialize dynamic codec registry", e);
                return false;
            }
        }
    }
    
    /**
     * Creates a dynamic codec loader that wraps the original loader using a dynamic proxy.
     * 
     * @param originalLoader The original Lucene codec loader
     * @return A custom loader proxy that provides dynamic fallbacks
     */
    private static Object createDynamicLoaderProxy(final Object originalLoader) {
        // Get all interfaces implemented by the original loader
        Class<?>[] interfaces = originalLoader.getClass().getInterfaces();
        
        // Create an invocation handler that intercepts method calls
        InvocationHandler handler = new InvocationHandler() {
            @Override
            public Object invoke(Object proxy, Method method, Object[] args) throws Throwable {
                // If the method being called is "lookup", handle it specially
                if (LOOKUP_METHOD_NAME.equals(method.getName()) && args != null && args.length == 1 
                        && args[0] instanceof String) {
                    String codecName = (String) args[0];
                    try {
                        // First try the standard lookup from the original loader
                        return method.invoke(originalLoader, args);
                    } catch (Exception e) {
                        // If lookup fails, try our dynamic provider
                        log.debug("Standard codec lookup failed for '{}', trying dynamic fallback", codecName);
                        return DynamicCodecProvider.getCodec(codecName);
                    }
                }
                
                // For all other methods, just pass through to the original loader
                return method.invoke(originalLoader, args);
            }
        };
        
        // Create and return a proxy that implements all the interfaces of the original loader
        return Proxy.newProxyInstance(
            originalLoader.getClass().getClassLoader(),
            interfaces,
            handler
        );
    }
    
    /**
     * Pre-registers any special codecs that need custom handling.
     * This is useful for codecs that are known to require special handling.
     * 
     * @param name The codec name
     * @param codec The codec instance
     */
    public static void registerSpecialCodec(String name, Codec codec) {
        try {
            // First make sure we're initialized
            if (!initialized && !initialize()) {
                log.warn("Cannot register special codec '{}' - registry initialization failed", name);
                return;
            }
            
            // Force Codec class to recognize our codec
            Method registerMethod = Codec.class.getDeclaredMethod("register", Codec.class);
            registerMethod.setAccessible(true);
            registerMethod.invoke(null, codec);
            
            log.info("Successfully registered special codec: {}", name);
        } catch (Exception e) {
            log.error("Failed to register special codec '{}'", name, e);
        }
    }
    
    /**
     * Gets the status of the registry initialization.
     * 
     * @return true if the registry has been successfully initialized
     */
    public static boolean isInitialized() {
        return initialized;
    }
}
