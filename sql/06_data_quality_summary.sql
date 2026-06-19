SELECT
    source_table,
    issue,
    COUNT(*) AS records_count
FROM dwh.etl_bad_records
GROUP BY source_table, issue
ORDER BY source_table, records_count DESC, issue;
