# Security Policy

## Reporting a vulnerability

If you discover a security issue in this project, please do not open a public GitHub issue. Instead, open a private security advisory at https://github.com/mushfiqmahim/bcra-project/security/advisories/new.

You can expect an initial response within 7 days.

## Scope

This project is a public dashboard with no user accounts, no telemetry, and no payment processing. The primary security concerns are:

- Accidental exposure of the Google Cloud service account credentials used to authenticate against Earth Engine.
- Vulnerabilities in dependencies tracked by `requirements.txt`.

The Streamlit Cloud deployment is sandboxed; the application code itself does not handle authenticated user data.
