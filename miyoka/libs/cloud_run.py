from logging import Logger
from google.cloud import run_v2
import threading
import time


class CloudRun:
    def __init__(
        self,
        logger: Logger,
        project: str,
        location: str,
        job_name: str,
    ) -> None:
        self.logger = logger
        self.project = project
        self.location = location
        self.job_name = job_name

    def schedule_analyze_in_background(self, *args, **kwargs):
        threading.Thread(target=self.schedule_analyze, args=args, kwargs=kwargs).start()

    def schedule_analyze(
        self,
        replay_id: str,
        initial_delay_sec: int = 0,
    ) -> None:
        time.sleep(initial_delay_sec)

        client = run_v2.JobsClient()

        job_name = (
            f"projects/{self.project}/locations/{self.location}/jobs/{self.job_name}"
        )

        overrides = run_v2.RunJobRequest.Overrides(
            container_overrides=[
                run_v2.RunJobRequest.Overrides.ContainerOverride(
                    env=[
                        run_v2.EnvVar(name="REPLAY_ANALYZER_REPLAY_ID", value=replay_id)
                    ],
                )
            ],
        )

        request = run_v2.RunJobRequest(name=job_name, overrides=overrides)

        operation = client.run_job(request=request)

        self.logger.info(f"Scheduled to run a job for {replay_id}")
