package org.opensearch.migrations;

import java.util.function.Predicate;

import lombok.experimental.UtilityClass;

@UtilityClass
public class VersionMatchers {
    public static final Predicate<Version> isES_6_8 = VersionMatchers.matchesMinorVersion(Version.fromString("ES 6.8"));
    public static final Predicate<Version> isES_7_X = VersionMatchers.matchesMajorVersion(Version.fromString("ES 7.10"));

    public static final Predicate<Version> isOpenSearch_2_X = VersionMatchers.matchesMajorVersion(Version.fromString("OS 2.0.0"));

    private static Predicate<Version> matchesMajorVersion(final Version version) {
        return other -> {
            var flavorMatches = version.getFlavor() == other.getFlavor();
            var majorVersionNumberMatches = version.getMajor() == other.getMajor();

            return flavorMatches && majorVersionNumberMatches;
        };
    }

    private static Predicate<Version> matchesMinorVersion(final Version version) {
        return other -> {
            return matchesMajorVersion(version)
                .and(other2 -> version.getMinor() == other2.getMinor())
                .test(other);
        };
    }
}
