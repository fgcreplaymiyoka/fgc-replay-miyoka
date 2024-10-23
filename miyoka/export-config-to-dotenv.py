from miyoka.container import Container
import os

def get_all_keys(d, parents=None):
    for key, value in d.items():
        keys = parents + [key] if parents else [key]
        if isinstance(value, dict):
            yield from get_all_keys(value, parents=keys)
        else:
            yield keys, value

if __name__ == "__main__":
    container = Container()
    config = container.config()

    with open(".env", "w") as f:
        for keys, value in get_all_keys(config):
            env_name = "MIYOKA_" + "_".join(keys).upper()
            f.write(f"{env_name}={value}\n")
