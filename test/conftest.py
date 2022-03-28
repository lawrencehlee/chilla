import pytest

from schemas import testing_schema


@pytest.fixture(autouse=True)
def clear_mongo_data():
    testing_schema.reset_everything()
