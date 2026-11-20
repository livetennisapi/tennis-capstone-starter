"""The real record on Zenodo. These tests download about 12 MB, so they run only when
CAPSTONE_NETWORK=1 is set. CI runs them in their own job.

The check for a newer version runs only with CAPSTONE_CHECK_LATEST=1, which CI sets on the
weekly and manual runs of the upstream repository. A class copy stays green when Zenodo
publishes a new version, because its pinned files do not change."""
from __future__ import annotations

import os

import pytest

from capstone import data

pytestmark = pytest.mark.skipif(os.environ.get('CAPSTONE_NETWORK') != '1',
                                reason='set CAPSTONE_NETWORK=1 to reach Zenodo')


@pytest.mark.skipif(os.environ.get('CAPSTONE_CHECK_LATEST') != '1',
                    reason='set CAPSTONE_CHECK_LATEST=1 to look for a newer version')
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
    assert str(points.timestamp_utc.dtype).startswith('datetime64')
    assert points.timestamp_utc.notna().all()
