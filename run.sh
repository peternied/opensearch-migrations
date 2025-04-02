
awscurl -X DELETE \
  -H "Content-Type: application/json" \
  --profile default \
  --region us-east-1 \
  --service aoss \
  https://REDACTED.us-east-1.aoss.amazonaws.com/migrations_working_state \
  -v

sleep 14

rm -rf /tmp/s3_files
rm -rf /tmp/lucene_files

./gradlew DocumentsFromSnapshotMigration:run --args="\
  --snapshot-name rfs-snapshot \
  --s3-local-dir /tmp/s3_files \
  --s3-repo-uri s3://REDACTED/rfs-snapshot-repo/ \
  --s3-region us-east-1 \
  --lucene-dir /tmp/lucene_files \
  --target-host https://REDACTED.us-east-1.aoss.amazonaws.com \
  --target-aws-region us-east-1 \
  --target-aws-service-signing-name aoss \
  --index-allowlist \"opensearch-000090\"" \
  || { exit_code=$?; [[ $exit_code -ne 3 ]] && echo "Command failed with exit code $exit_code. Consider rerunning the command."; }

