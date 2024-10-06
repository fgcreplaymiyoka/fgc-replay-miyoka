import shutil
import os
import time


def cleanup_dir(dir_path):
    shutil.rmtree(dir_path, ignore_errors=True)
    os.mkdir(dir_path)


def retry(max_retries=3, delay=2):
    def retry_decorator(func):
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    print(f"Attempt {retries + 1} failed: {e}")
                    retries += 1
                    time.sleep(delay)
            raise Exception(f"Failed after {max_retries} attempts")

        return wrapper

    return retry_decorator
