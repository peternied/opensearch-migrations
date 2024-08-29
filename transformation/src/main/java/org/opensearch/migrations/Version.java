package org.opensearch.migrations;

import lombok.Builder;
import lombok.EqualsAndHashCode;
import lombok.Getter;
import lombok.RequiredArgsConstructor;

@RequiredArgsConstructor
@Getter
@Builder
@EqualsAndHashCode
public class Version {
    private final Flavor flavor;
    private final int major;
    private final int minor;
    private final int patch;

    public String toString() {
        return String.format("%s %d.%d.%d", flavor.name(), major, minor, patch);
    }

    /** TODO: Do not merge this code, do something smarter */
    public boolean matches(Version that) {
        if (that == null) {
            return false;
        }
        
        if (this.flavor != that.flavor) {
            return false;
        }

        if (this.major != that.major) {
            return false;
        }

        if (this.flavor == Flavor.OpenSearch) {
            // All major versions of OpenSearch are compatible with one another
            return true;
        }

        if (this.minor != that.minor) {
            return false;
        }
        
        // All patch versions are considered compatible with one another
        return true;
    }

    public static Version fromString(final String raw) throws RuntimeException {
        var builder = Version.builder();
        var remainingString = raw.toLowerCase();

        for (var flavor : Flavor.values()) {
            if (remainingString.startsWith(flavor.name().toLowerCase())) {
                remainingString = remainingString.substring(flavor.name().length());
                builder.flavor(flavor);
                break;
            } else if (remainingString.startsWith(flavor.shorthand.toLowerCase())) {
                remainingString = remainingString.substring(flavor.shorthand.length());
                builder.flavor(flavor);
                break;
            }
        }

        if (remainingString.equals(raw.toLowerCase())) {
            throw new RuntimeException("Unable to determine build flavor from '" + raw +"'");
        }

        try {
            // Remove any spaces
            remainingString = remainingString.trim();
            // Remove any _ separators from the digits
            remainingString = remainingString.replaceFirst("^_+", "");

            // Break out into the numeric parts
            var versionParts = remainingString.split("[\\._]");

            builder.major(Integer.parseInt(versionParts[0]));

            if (versionParts.length > 1) {
                builder.minor(versionParts[1].equals("x") ? 0 : Integer.parseInt(versionParts[1]));
            }

            if (versionParts.length > 2) {
                builder.patch(versionParts[2].equals("x") ? 0 : Integer.parseInt(versionParts[2]));
            }
            return builder.build();
        } catch (Exception e) {
            throw new RuntimeException("Unable to parse version numbers from the string '" + raw + "'\r\n", e);
        }
    }
}
