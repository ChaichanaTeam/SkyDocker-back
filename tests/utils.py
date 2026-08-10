import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import random
import string


def random_email():
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"testuser_{suffix}@localhost.me"


def random_phone():
    number = "+48" + ''.join(random.choices(string.digits, k=9))

    return number