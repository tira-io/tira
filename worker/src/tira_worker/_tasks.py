from celery import Celery

# TODO: make configurable using tira-application-config.yml
backend_url = "rpc://localhost"
broker_url = "amqp://localhost"

app = Celery("tira-tasks", backend=backend_url, broker=broker_url)


@app.task
def evaluate(text: str):
    # TODO: Implement me
    from time import sleep

    sleep(2)
    return f"Hello {text}"
