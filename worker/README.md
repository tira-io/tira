# Install

`pip install -e .`

# Start a Worker
> [!NOTE]
> If you want to launch multiple workers on the same machine, use the `-n <name>` option.

```bash
celery -A tira_worker:app worker -l INFO
```
