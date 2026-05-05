import ee


def init_ee() -> None:
    ee.Initialize(project="earth-engine-project-495404")


def test_connection():
    return ee.Number(10).add(5).getInfo()
