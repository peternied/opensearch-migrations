package org.opensearch.migrations.bulkload.workcoordination;

import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.SQLException;

public interface AbstractedDatabaseClient extends AutoCloseable {
    <T> T executeInTransaction(TransactionFunction<T> operation) throws SQLException;
    <T> T executeQuery(String sql, ResultSetMapper<T> mapper, Object... params) throws SQLException;
    int executeUpdate(String sql, Object... params) throws SQLException;
    
    @FunctionalInterface
    interface TransactionFunction<T> {
        T apply(Connection conn) throws SQLException;
    }
    
    @FunctionalInterface
    interface ResultSetMapper<T> {
        T map(ResultSet rs) throws SQLException;
    }
}
