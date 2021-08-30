from datetime import datetime


def get_tira_id():
    dt = datetime.now()
    return dt.strftime("%Y-%m-%d-%H-%M-%S")
