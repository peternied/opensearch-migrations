package org.opensearch.migrations.bulkload.lucene.version_9;

import java.lang.reflect.Field;
import java.lang.reflect.InvocationHandler;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;

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
    private static final String HOLDER_CLASS_NAME = "Holder";
    private static final String LOADER_FIELD_NAME = "LOADER";
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
                // Access the static inner Holder class
                Class<?>[] innerClasses = Codec.class.getDeclaredClasses();
                Class<?> holderClass = null;
                for (Class<?> innerClass : innerClasses) {
                    if (HOLDER_CLASS_NAME.equals(innerClass.getSimpleName())) {
                        holderClass = innerClass;
                        break;
                    }
                }
                
                if (holderClass == null) {
                    throw new NoSuchFieldException("Could not find Holder inner class in Codec");
                }
                
                // Access the private static 'LOADER' field in the Holder class
                Field loaderField = holderClass.getDeclaredField(LOADER_FIELD_NAME);
                loaderField.setAccessible(true);
                
                // Get the current loader instance
                Object originalLoader = loaderField.get(null);
                
                // Create our custom loader wrapping the original one
                Object dynamicLoader = createDynamicLoaderProxy(originalLoader);
                
                // Use Unsafe to modify the final field
                try {
                    Class<?> unsafeClass = Class.forName("sun.misc.Unsafe");
                    Field unsafeField = unsafeClass.getDeclaredField("theUnsafe");
                    unsafeField.setAccessible(true);
                    Object unsafe = unsafeField.get(null);
                    
                    Method putObjectMethod = unsafeClass.getMethod("putObject", Object.class, long.class, Object.class);
                    Method staticFieldOffsetMethod = unsafeClass.getMethod("staticFieldOffset", Field.class);
                    long offset = (Long) staticFieldOffsetMethod.invoke(unsafe, loaderField);
                    putObjectMethod.invoke(unsafe, holderClass, offset, dynamicLoader);
                } catch (ClassNotFoundException e) {
                    // Try jdk.internal.misc.Unsafe for newer JDK versions
                    Class<?> unsafeClass = Class.forName("jdk.internal.misc.Unsafe");
                    Field unsafeField = unsafeClass.getDeclaredField("theUnsafe");
                    unsafeField.setAccessible(true);
                    Object unsafe = unsafeField.get(null);
                    
                    Method putObjectMethod = unsafeClass.getMethod("putObject", Object.class, long.class, Object.class);
                    Method staticFieldOffsetMethod = unsafeClass.getMethod("staticFieldOffset", Field.class);
                    long offset = (Long) staticFieldOffsetMethod.invoke(unsafe, loaderField);
                    putObjectMethod.invoke(unsafe, holderClass, offset, dynamicLoader);
                }
                
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
     * @param originalLoader The original Lucene codec loader (NamedSPILoader)
     * @return A custom loader proxy that provides dynamic fallbacks
     */
    private static Object createDynamicLoaderProxy(final Object originalLoader) {
        // Create an invocation handler that intercepts method calls
        InvocationHandler handler = new InvocationHandler() {
            @Override
            public Object invoke(Object proxy, Method method, Object[] args) throws Throwable {
                String methodName = method.getName();
                
                // Handle lookup method specially (NamedSPILoader specific)
                if (LOOKUP_METHOD_NAME.equals(methodName) && args != null && args.length == 1 
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
                
                // Handle Map.get method specially (Map interface) - this is likely used by Codec.forName()
                if ("get".equals(methodName) && args != null && args.length == 1 
                        && args[0] instanceof String) {
                    String codecName = (String) args[0];
                    try {
                        // First try the standard get from the original loader
                        return method.invoke(originalLoader, args);
                    } catch (Exception e) {
                        // If get fails, try our dynamic provider
                        log.debug("Standard codec get failed for '{}', trying dynamic fallback", codecName);
                        return DynamicCodecProvider.getCodec(codecName);
                    }
                }
                
                // For all other methods, just pass through to the original loader
                return method.invoke(originalLoader, args);
            }
        };
        
        // Get all interfaces implemented by the original loader
        Class<?>[] interfaces = originalLoader.getClass().getInterfaces();
        
        // Create and return a proxy that implements all the interfaces of the original loader
        return Proxy.newProxyInstance(
            originalLoader.getClass().getClassLoader(),
            interfaces,
            handler
        );
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
