import os

# Override db name before any tests get executed
os.environ["CHILLA_MONGO_DATABASE_NAME"] = "Chilla_test"
