package org.opensearch.migrations.transformation;

import lombok.Getter;
import lombok.RequiredArgsConstructor;

/**
 * The result after checking if a transformer can be applied to an entity
 */
public abstract class CanApplyResult {
    private CanApplyResult() {}

    private static class Holder {
        static final CanApplyResult YES = new Yes();
        static final CanApplyResult NO = new No();
    }

    public static final CanApplyResult YES = Holder.YES;
    public static final CanApplyResult NO = Holder.NO;

    /** Yes, the transformation can be applied */
    public static final class Yes extends CanApplyResult {}

    /** No, the transformation cannot be applied */
    public static final class No extends CanApplyResult {}

    /** While the transformation matches the scenario but there is an issue that would prevent it from being applied corrrectly */
    @RequiredArgsConstructor
    @Getter
    public static final class Unsupported extends CanApplyResult {
        private final String reason;
    }
}
