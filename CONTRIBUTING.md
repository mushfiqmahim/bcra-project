# Contributing

Thank you for your interest in the Bangladesh Climate Risk Atlas.

## Local development

```bash
git clone https://github.com/mushfiqmahim/bcra-project.git
cd bcra-project
pip install -r requirements.txt
earthengine authenticate
streamlit run app.py
```

You will need a Google account with Earth Engine access. See https://earthengine.google.com to register.

## Running smoke tests

Each indicator has a smoke test in `scripts/`:

```bash
python scripts/verify_ndvi.py
python scripts/verify_flood.py
python scripts/verify_salinity.py
```

These exercise each module against the live Earth Engine API and assert basic invariants on the returned values.

## Reporting issues

Open an issue at https://github.com/mushfiqmahim/bcra-project/issues with steps to reproduce, expected behavior, and observed behavior.

## Pull requests

- Branch from `main`.
- One logical change per PR.
- Run the relevant `verify_*.py` script locally before submitting.
- Update `docs/project_spec.md` if your change affects the architecture.
