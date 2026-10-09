from importlib.util import find_spec
import pytest


def test_smoke():
    # Test image ships without backend sources
    if find_spec("backend_src") is None:
        pytest.skip("backend_src is not available in this environment")

    try:
        from backend_src import main
    except (ImportError, AttributeError):
        assert False, "Circular\\Invalid import found"