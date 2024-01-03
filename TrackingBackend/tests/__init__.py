import os

os.environ["ETVR_UNITTEST"] = "1"
if not os.path.exists(".pytest_cache"):
    os.mkdir(".pytest_cache")
