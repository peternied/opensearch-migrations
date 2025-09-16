package org.opensearch.migrations.bulkload.lucene.version_9;

import lombok.extern.slf4j.Slf4j;
import shadow.lucene9.org.apache.lucene.codecs.Codec;
import shadow.lucene9.org.apache.lucene.codecs.CompoundFormat;
import shadow.lucene9.org.apache.lucene.codecs.DocValuesFormat;
import shadow.lucene9.org.apache.lucene.codecs.FieldInfosFormat;
import shadow.lucene9.org.apache.lucene.codecs.KnnVectorsFormat;
import shadow.lucene9.org.apache.lucene.codecs.LiveDocsFormat;
import shadow.lucene9.org.apache.lucene.codecs.NormsFormat;
import shadow.lucene9.org.apache.lucene.codecs.PointsFormat;
import shadow.lucene9.org.apache.lucene.codecs.PostingsFormat;
import shadow.lucene9.org.apache.lucene.codecs.SegmentInfoFormat;
import shadow.lucene9.org.apache.lucene.codecs.StoredFieldsFormat;
import shadow.lucene9.org.apache.lucene.codecs.TermVectorsFormat;

/**
 * A dynamic fallback codec that proxies all operations to a base codec.
 * This is used to handle unknown codecs encountered during index reading
 * without requiring explicit registration for each one.
 */
@Slf4j
public class DynamicFallbackCodec extends Codec {
    
    private final Codec baseCodec;
    
    /**
     * Creates a dynamic fallback codec with the given name.
     * 
     * @param name The name of the codec to emulate
     * @param baseCodecName The name of the base codec to delegate to
     */
    public DynamicFallbackCodec(String name, String baseCodecName) {
        super(name);
        Codec tempCodec;
        try {
            tempCodec = Codec.forName(baseCodecName);
            log.info("Created dynamic fallback for codec '{}' using base codec '{}'", name, baseCodecName);
        } catch (IllegalArgumentException e) {
            // If the base codec doesn't exist, fall back to a known good one
            log.warn("Base codec '{}' not found, falling back to Lucene94", baseCodecName);
            tempCodec = Codec.forName("Lucene94");
        }
        this.baseCodec = tempCodec;
    }

    @Override
    public PostingsFormat postingsFormat() {
        return baseCodec.postingsFormat();
    }

    @Override
    public DocValuesFormat docValuesFormat() {
        return baseCodec.docValuesFormat();
    }

    @Override
    public StoredFieldsFormat storedFieldsFormat() {
        return baseCodec.storedFieldsFormat();
    }

    @Override
    public TermVectorsFormat termVectorsFormat() {
        return baseCodec.termVectorsFormat();
    }

    @Override
    public FieldInfosFormat fieldInfosFormat() {
        return baseCodec.fieldInfosFormat();
    }

    @Override
    public SegmentInfoFormat segmentInfoFormat() {
        return baseCodec.segmentInfoFormat();
    }

    @Override
    public NormsFormat normsFormat() {
        return baseCodec.normsFormat();
    }

    @Override
    public LiveDocsFormat liveDocsFormat() {
        return baseCodec.liveDocsFormat();
    }

    @Override
    public CompoundFormat compoundFormat() {
        return baseCodec.compoundFormat();
    }

    @Override
    public PointsFormat pointsFormat() {
        return baseCodec.pointsFormat();
    }

    @Override
    public KnnVectorsFormat knnVectorsFormat() {
        // Use our own IgnoreVectorsFormat which is a no-op implementation
        // This is safer than using baseCodec.knnVectorsFormat() which might not
        // handle proprietary vector formats
        return new IgnoreVectorsFormat();
    }
}
