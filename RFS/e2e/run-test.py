import argparse

def create_source_cluster():
    pass

def create_target_cluster():
    pass

def load_data(source):
    pass

def perform_migration(source, target):
    pass

def collect_results():
    pass

def clean_up_resources(resources):
    pass

def summarize_results():
    pass


def main():
    parser = argparse.ArgumentParser(description="Run end to end test suite")
    parser.add_argument("--migration-tool", choices=['rfs', 'osi'], help="Which migration tool to use to run the end to end scenario", required=True)

    args = parser.parse_args()

    print(f"Arguments: {args}")

    # Setup 
    source_cluster = create_source_cluster()
    target_cluster = create_target_cluster()
    load_data(source_cluster)

    # Run Migration
    migration_tool_resources = perform_migration(source_cluster, target_cluster)

    # Collect everything post migration
    results = collect_results()
    clean_up_resources([source_cluster, target_cluster, migration_tool_resources])
    summarize_results()

if __name__ == "__main__":
    main()