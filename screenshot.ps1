# Make UTF8 default encoding in Python, otherwise multi-byte chracters in config.yaml can't be loaded in Windows.
# https://stackoverflow.com/a/50933341
$Env:PYTHONUTF8 = "1"

poetry run python miyoka/screenshot.py

