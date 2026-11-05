"""Read-only guide with the results of a real run under every step - no Snowflake connection needed."""
from app_main import main

main(dry_run=True)
