from importlib.util import find_spec


# The test image ships without backend sources, these tests import them
collect_ignore_glob = ["test_*.py"] if find_spec("backend_src") is None else []
