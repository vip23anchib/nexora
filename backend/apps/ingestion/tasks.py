import logging

from celery import shared_task

from .services import process_import_job

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=10,
    acks_late=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
)
def run_import_job_task(self, job_id):
    """
    Asynchronous worker task that executes the data ingestion pipeline.
    Utilizes late acknowledgment and bounded retries with backoff.
    """
    logger.info("Executing async ingestion job task for job_id: %s", job_id)
    try:
        job = process_import_job(job_id)
        if job:
            logger.info("Ingestion completed for job %s with status: %s", job.id, job.status)
        return job_id
    except Exception as exc:
        logger.exception("Ingestion task failed for job %s: %s", job_id, exc)
        raise exc
