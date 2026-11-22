import json
import health

print(json.dumps(health.recent_runs(4), indent=2))
print(json.dumps(health.failed_checks(3), indent=2))