# Install

`pip install -e .`

# Start a Worker
> [!NOTE]
> If you want to launch multiple workers on the same machine, use the `-n <name>` option.

```bash
celery -A tira_worker:app worker -l INFO
```

# Testing it
```py
from celery.app.control import Inspect
from celery.result import AsyncResult
from tira_worker import app, evaluate

if __name__ == "__main__":
    # List all registered workers
    inspect: Inspect = app.control.inspect()
    workers = inspect.active()
    print(f"I found {len(workers)} active workers")
    for name, worker in workers.items():
        print(f"\t{name}")

    # Start a job
    result: AsyncResult = evaluate.delay("Maik")
    print(result.status)
    print(next(result.collect())[1])
    print(result.status)
```