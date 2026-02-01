from celery import shared_task
from .services import fetch_external_alerts


@shared_task
def fetch_alerts_task(url):
    """
    Background task to fetch alerts from external API.

    :param url: The URL to fetch alerts from
    :return: The fetched data
    """
    try:
        data = fetch_external_alerts(url)
        # Here you could process the data, e.g., create Alert objects
        return data
    except Exception as e:
        # Log error or handle
        raise e