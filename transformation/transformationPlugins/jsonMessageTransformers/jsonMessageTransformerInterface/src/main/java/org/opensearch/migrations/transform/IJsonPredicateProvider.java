package org.opensearch.migrations.transform;

import lombok.NonNull;

public interface IJsonPredicateProvider {
    /**
     * Create a new Predicate from the given configuration.  This Predicate
     * will be used repeatedly and concurrently from different threads against
     * messages.
     * @param jsonConfig is a List, Map, String, or null that should be used to configure the
     *                   IJsonPredicate that is being created
     */
    IJsonPredicate createPredicate(Object jsonConfig);

    /**
     * Friendly name that can be used as a key to identify Predicate providers.
     */
    default @NonNull String getName() {
        return this.getClass().getSimpleName();
    }
}
