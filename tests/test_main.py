import os
import sys
import types
from unittest.mock import patch, Mock

# Ensure src is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import importlib


def _import_main_with_fake_p4(run_describe_return):
    """Insert a fake P4 module into sys.modules and import (or reload) main.

    Returns the imported main module.
    """
    fake_p4 = types.ModuleType('P4')

    class P4Class:
        def __init__(self):
            self.user = None
            self.port = None

        def connect(self):
            # no-op so import doesn't attempt real connection
            return None

        def run_describe(self, changelist):
            return run_describe_return

    fake_p4.P4 = P4Class
    fake_p4.P4Exception = Exception

    # insert into sys.modules before importing main
    sys.modules['P4'] = fake_p4

    # ensure main is freshly imported
    if 'src.main' in sys.modules:
        del sys.modules['src.main']
    if 'main' in sys.modules:
        del sys.modules['main']

    main = importlib.import_module('main')
    importlib.reload(main)
    return main


def test_gather_changelist_links():
    # do not need P4 for this helper
    from main import gather_changelist_links

    desc = 'This CL updates textures (http://example.com/preview.jpg) and docs.'
    links = gather_changelist_links(desc)
    assert isinstance(links, list)
    assert 'http://example.com/preview.jpg' in links


def test_gather_cr_links_behavior():
    # Current behavior uses re.match so only leading digits match
    from main import gather_cr_links

    # leading digits should match
    m = gather_cr_links('12345 fixed bug')
    assert m is not None
    assert getattr(m, 'group')() == '12345'

    # digits in middle do not match with re.match
    m2 = gather_cr_links('see 12345 for details')
    assert m2 is None


def test_main_calls_attach_weblink_per_file_and_link():
    # Create run_describe return with two depot files and one weblink in desc
    run_desc = [
        {
            'desc': 'Update textures (http://example.com/img.png)',
            'depotFile': ['//depot/a.png', '//depot/b.png'],
        }
    ]

    main = _import_main_with_fake_p4(run_desc)

    # patch attach_weblink in the imported main module so we don't perform network calls
    with patch.object(main, 'attach_weblink') as mock_attach:
        main.main('42')

        # expect 2 files * 1 link = 2 calls
        assert mock_attach.call_count == 2

        called_args = [call[0] for call in mock_attach.call_args_list]
        # each call args tuple (depot_file, weblink)
        assert ('//depot/a.png', 'http://example.com/img.png') in called_args
        assert ('//depot/b.png', 'http://example.com/img.png') in called_args
