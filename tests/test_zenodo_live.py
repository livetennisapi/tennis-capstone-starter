"""The real record on Zenodo. These tests download about 12 MB, so they run only when
CAPSTONE_NETWORK=1 is set. CI runs them in their own job."""
from __future__ import annotations

import os

import pytest

from capstone import data

pytestmark = pytest.mark.skipif(os.environ.get('CAPSTONE_NETWORK') != '1',
                                reason='set CAPSTONE_NETWORK=1 to reach Zenodo')


def test_the_concept_doi_still_resolves_to_the_pinned_version():
    """Fails when a newer version is published, so the pins get a look."""
    import json
    with data._get(data.record_url(data.CONCEPT_DOI)) as resp:
        latest = json.load(resp)
    assert latest['doi'] == data.VERSION_DOI
    assert latest['metadata']['license']['id'] == 'cc-by-nc-4.0'


def test_the_pinned_files_download_and_match(tmp_path):
    folder = os.environ.get('CAPSTONE_DATA_DIR') or tmp_path
    data.download(folder)
    data.check(folder)
    assert len(data.load_players(folder)) == 32678
    assert len(data.load_matches(folder)) == 173571
    points = data.load_points(folder)
    assert len(points) == 951064
    assert points.match_id.nunique() == 5380
