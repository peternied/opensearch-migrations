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
 * Fallback codec for KNN87Codec that allows reading indices without requiring the actual KNN implementation.
 * This codec delegates to Lucene94 for most operations but uses our own IgnoreVectorsFormat for KNN vectors.
 */
@Slf4j
public class KNN87Codec extends Codec {
    private static final String BASE_CODEC_NAME = "Lucene94";
    
    public KNN87Codec() {
        super("KNN87Codec");
        log.info("Created fallback KNN87Codec - KNN vector data will not be available");
    }

    @Override
    public PostingsFormat postingsFormat() {
        return Codec.forName(BASE_CODEC_NAME).postingsFormat();
    }

    @Override
    public DocValuesFormat docValuesFormat() {
        return Codec.forName(BASE_CODEC_NAME).docValuesFormat();
    }

    @Override
    public StoredFieldsFormat storedFieldsFormat() {
        return Codec.forName(BASE_CODEC_NAME).storedFieldsFormat();
    }

    @Override
    public TermVectorsFormat termVectorsFormat() {
        return Codec.forName(BASE_CODEC_NAME).termVectorsFormat();
    }

    @Override
    public FieldInfosFormat fieldInfosFormat() {
        return Codec.forName(BASE_CODEC_NAME).fieldInfosFormat();
    }

    @Override
    public SegmentInfoFormat segmentInfoFormat() {
        return Codec.forName(BASE_CODEC_NAME).segmentInfoFormat();
    }

    @Override
    public NormsFormat normsFormat() {
        return Codec.forName(BASE_CODEC_NAME).normsFormat();
    }

    @Override
    public LiveDocsFormat liveDocsFormat() {
        return Codec.forName(BASE_CODEC_NAME).liveDocsFormat();
    }

    @Override
    public CompoundFormat compoundFormat() {
        return Codec.forName(BASE_CODEC_NAME).compoundFormat();
    }

    @Override
    public PointsFormat pointsFormat() {
        return Codec.forName(BASE_CODEC_NAME).pointsFormat();
    }

    @Override
    public KnnVectorsFormat knnVectorsFormat() {
        // Use our own IgnoreVectorsFormat which is a no-op implementation
        return new IgnoreVectorsFormat();
    }
}
