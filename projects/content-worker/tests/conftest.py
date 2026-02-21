"""Pytest configuration for content-worker pipeline tests."""


def pytest_addoption(parser):
    parser.addoption(
        "--integration",
        action="store_true",
        default=False,
        help="Run integration tests (costs ~$0.50, takes ~3 min)",
    )
