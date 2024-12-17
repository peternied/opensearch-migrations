export default function MigrationAssistantVersion({ versionIdentifier } : { versionIdentifier: string}) {
  return (
    <>
      Migration Assistant version <code>{versionIdentifier}</code>.
    </>
  );
}
