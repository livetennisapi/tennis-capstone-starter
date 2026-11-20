<a href="https://livetennisapi.com"><img src="assets/logo.svg" alt="Live Tennis API logo" width="72" height="72"></a>

# tennis-capstone-starter

**Starter code for "Does the score predict the match?", a tennis capstone for data science and statistics courses from [Live Tennis API](https://livetennisapi.com).**

[Website](https://livetennisapi.com) · [Capstone brief](https://livetennisapi.com/teach/capstone) · [Docs](https://docs.livetennisapi.com) · [Win probability calculator](https://livetennisapi.com/tools/win-probability) · [Academic dataset](https://livetennisapi.com/data/academic) · [Pricing](https://livetennisapi.com/pricing) · [Dashboard](https://livetennisapi.com/account/) · [Changelog](https://docs.livetennisapi.com/changelog.html)

[![CI](https://github.com/livetennisapi/tennis-capstone-starter/actions/workflows/ci.yml/badge.svg)](https://github.com/livetennisapi/tennis-capstone-starter/actions/workflows/ci.yml)
[![Data DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22048730.svg)](https://doi.org/10.5281/zenodo.22048730)
[![Code: MIT](https://img.shields.io/badge/code-MIT-green.svg)](LICENSE)
[![Data: CC BY-NC 4.0](https://img.shields.io/badge/data-CC%20BY--NC%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc/4.0/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](pyproject.toml)

From any score in a tennis match, a simple model gives each player a chance of winning. If it says 70%, do those players win about 70% of the time? In this capstone, students rebuild that model and test it on real professional matches. Then they write up where it breaks.

The full brief, with the rubric and the hours for each milestone, is at [livetennisapi.com/teach/capstone](https://livetennisapi.com/teach/capstone).

## Get started

You need Python 3.11 or newer. No API key and no account.

```bash
git clone https://github.com/livetennisapi/tennis-capstone-starter.git
cd tennis-capstone-starter
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev,notebook]"
python -m capstone.data            # download the data and check it
pytest                             # the loader tests pass, the model checks skip
jupyter lab notebooks/
```

`python -m capstone.data` prints this on the first run:

```text
matches.csv.gz: downloading 2,430,730 bytes from Zenodo
matches.csv.gz: checksums match
players.csv.gz: downloading 420,351 bytes from Zenodo
players.csv.gz: checksums match
points_sample_2026-06.csv.gz: downloading 9,377,769 bytes from Zenodo
points_sample_2026-06.csv.gz: checksums match
Done. Data under CC BY-NC 4.0: https://creativecommons.org/licenses/by-nc/4.0/
```

A second run finds the files in `data/` and downloads nothing. `python -m capstone.data --check` checks them without the network. To keep the data somewhere else, on Colab for example, set `CAPSTONE_DATA_DIR` to a folder.

## The four milestones

| Milestone | Notebook | Hours |
| --- | --- | --- |
| 1. Load and clean the sample | [`01-load-and-clean.ipynb`](notebooks/01-load-and-clean.ipynb) | 6 |
| 2. Rebuild the model | [`02-rebuild-the-model.ipynb`](notebooks/02-rebuild-the-model.ipynb) and [`src/capstone/model.py`](src/capstone/model.py) | 10 |
| 3. Measure calibration | [`03-calibration.ipynb`](notebooks/03-calibration.ipynb) | 8 |
| 4. Write up where the model breaks | [`04-where-the-model-breaks.ipynb`](notebooks/04-where-the-model-breaks.ipynb) | 6 |

The hours are our estimate for a student who knows pandas and basic probability.

In milestone 2, students write five functions in `src/capstone/model.py`: `hold`, `tiebreak`, `set_win`, `match_win` and `match_win_from`. It is the same independent-points model as the [win probability calculator](https://livetennisapi.com/tools/win-probability). `tests/test_model.py` checks them against the calculator's figures. At 64% and 62% of points won on serve, the calculator shows holds of 81.3% and 77.6%. The set is 56.7% and a best of three match 59.9%. Each check skips until its function stops raising `NotImplementedError`.

## The data

The data is the public sample of the Live Tennis API point-by-point dataset, DOI [10.5281/zenodo.22048730](https://doi.org/10.5281/zenodo.22048730) on Zenodo. This starter is pinned to version 1.0.3, published on 28 October 2026, so a whole class works on the same bytes. Its own DOI is [10.5281/zenodo.23718893](https://doi.org/10.5281/zenodo.23718893).

| File | Rows | A row is |
| --- | --- | --- |
| `matches.csv.gz` | 173,571 | One completed match, 1 January 2023 to 13 August 2026 |
| `players.csv.gz` | 32,678 | One player, with country, birth date and playing hand |
| `points_sample_2026-06.csv.gz` | 951,064 | One score state, for 5,380 completed matches of June 2026 |

[`src/capstone/data.py`](src/capstone/data.py) asks the Zenodo API for the record and refuses any version but 1.0.3. It checks each file's size, the MD5 checksum Zenodo lists and a SHA-256 checksum pinned in the code. A file that fails is deleted, never used.

Read the [record's](https://zenodo.org/records/23718893) own `README.md` and `DATA_DICTIONARY.md` before milestone 1.

**Licence.** The data is under [Creative Commons Attribution NonCommercial 4.0 International (CC BY-NC 4.0)](https://creativecommons.org/licenses/by-nc/4.0/), as the Zenodo record states. You may use it for coursework and research with credit to Live Tennis API, but not for commercial work. It is not part of this repository and is not covered by its MIT licence. The loader puts it in `data/`, which git ignores.

The record asks for a citation. In BibTeX:

```bibtex
@dataset{livetennisapi_2026_point_by_point,
  author    = {{Live Tennis API}},
  title     = {Tennis Point-by-Point Dataset — ATP, WTA, Challenger, ITF (Public Sample)},
  year      = {2026},
  version   = {1.0.3},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.23718893},
  url       = {https://doi.org/10.5281/zenodo.22048730}
}
```

The full dataset is free for non-commercial academic research and teaching, on application to research@livetennisapi.com. See the [academic dataset page](https://livetennisapi.com/data/academic).

## What is in the repository

| Path | What it does |
| --- | --- |
| `src/capstone/data.py` | Downloads the sample by DOI, checks the checksums, loads each file as a DataFrame |
| `src/capstone/model.py` | The five model functions, for students to write |
| `notebooks/` | One notebook per milestone, with the tasks and empty cells |
| `tests/test_data.py` | The loader against a fake Zenodo, offline |
| `tests/test_model.py` | The milestone 2 checks |
| `tests/test_notebooks.py` | The notebooks are valid and ship without outputs |
| `tests/test_zenodo_live.py` | The real record and files, run with `CAPSTONE_NETWORK=1` |

## For teachers

The repository has no worked solutions, so you can hand it out for graded work. The rubric is on [the brief](https://livetennisapi.com/teach/capstone#rubric). CI runs the offline tests on Python 3.11, 3.13 and 3.14. A second job downloads the real files from Zenodo and checks them. The repository is a template, so **Use this template** on GitHub makes a class copy with the same checks. In a class copy, a student's model turns the skipped checks into passes or failures.

Tell us how it went at hello@livetennisapi.com. We never publish anything about a class without the teacher's consent. Problems with the starter are welcome as [issues](https://github.com/livetennisapi/tennis-capstone-starter/issues).

## Licence

The code is MIT. See [LICENSE](LICENSE). The data keeps its own licence, CC BY-NC 4.0, as above.
