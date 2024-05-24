import tomli

config = None

if config is None:
    with open("config.toml", "rb") as f:
        config = tomli.load(f)