# Smart Expense Tracker

A Django-based personal expense tracking application. The checked-in Python code defines authenticated account access, per-user expense records, category suggestions based on description keywords, spending summaries, and CSV/PDF report generation. The repository currently contains the application files at its root, while the Django settings and imports expect package and asset/template directories that are not present in the committed tree; see [Repository layout and run status](#repository-layout-and-run-status) before attempting to start it.

## Problem statement

Personal spending can be difficult to review when individual purchases, bills, and other transactions are not recorded consistently. This project provides a web interface for entering expenses, organizing them by category and date, and reviewing totals and downloadable reports.

## Objectives

- Keep expense records associated with the signed-in user.
- Support common expense categories and validate that amounts are positive.
- Make it easier to find and review transactions using text search, date/category filters, sorting, and pagination.
- Summarize spending in a dashboard and reports, and provide CSV and PDF downloads.
- Offer simple keyword-based category suggestions while entering an expense.

## Implemented features

The items below are reflected in the checked-in views, forms, models, utilities, templates, and tests:

- Account registration, login, logout, profile details editing, and password changes using Django authentication.
- Create, edit, view, and delete expense records. Expense queries for the main application are scoped to the current user.
- Expense fields for description, amount, category, date, optional notes, and created/updated timestamps. Amounts must be greater than zero.
- Eight categories: Food, Travel, Bills, Entertainment, Healthcare, Education, Shopping, and Other.
- Description-keyword category suggestions in the browser, plus a Django JSON endpoint and Python keyword predictor. This is rule-based matching, not a machine-learning model.
- Dashboard totals for today, the current week, the current month, and all time; recent expenses; a category breakdown; and a six-month spending trend chart.
- Expense history with description/notes search, preset or custom date filters, category filtering, amount/date sorting, totals, and pagination.
- Filterable reports with total, transaction count, average transaction amount, category breakdown, and a records preview.
- CSV and PDF exports based on the selected filters. PDF output is generated with ReportLab.
- Django admin registration for Expense, including list filters, search, date hierarchy, and ordering.
- A `seed_data.py` demo-data command is present in the source; it creates a `demo` user and sample expenses when installed in the expected Django command package layout. Its sample credentials are for demonstration only and must not be used in a real deployment.

## Technologies and libraries

### Server-side

- Python
- Django (the settings module's generated-file header identifies Django 6.1.2; no dependency manifest or supported-version declaration is included)
- SQLite, configured as Django's default database
- ReportLab for PDF report generation

The CSV, JSON, date calculations, and other utilities also use Python's standard library. The project uses Django's built-in authentication, forms, ORM, admin, templates, messages, and pagination.

### Browser-side

- Django HTML templates, HTML, CSS, and JavaScript
- Bootstrap 5.3.3 and Bootstrap Icons 1.11.3 via CDN
- Chart.js 4.4.2 via CDN for dashboard charts
- Inter font via Google Fonts

There is no JavaScript package manifest in the repository. The frontend libraries above are loaded from external URLs in the base template, so the browser needs network access to those CDNs for the corresponding styling, icons, charts, and font.

## Project structure

The checked-in tree at the documented commit contains root-level files rather than the conventional Django project/app/template/static folders:

```text
.
├── README.md
├── manage.py
├── settings.py, urls.py, asgi.py, wsgi.py   Django project configuration files
├── models.py, views.py, forms.py, admin.py  Expense app code (checked in at root)
├── utils.py                                Category rules and CSV/PDF report helpers
├── tests.py                                Django tests
├── seed_data.py                            Demo account and sample expense command source
├── *.html                                  Templates (checked in at root)
├── style.css, main.js                      Frontend assets (checked in at root)
├── db.sqlite3                              SQLite database file
├── launch.json, .hintrc                    Editor/browser configuration
└── *.cpython-314.pyc                       Checked-in Python bytecode files
```

Notable source files include `models.py` (`Expense`), `forms.py` (`ExpenseForm`, registration and profile forms), `views.py` (authentication, dashboard, expense, report, export, and profile handlers), and `utils.py` (category rules and report generation). Templates present at the root include `base.html`, `dashboard.html`, `expense_list.html`, `add_expense.html`, `edit_expense.html`, `delete_expense.html`, `reports.html`, `profile.html`, `login.html`, and `register.html`.

## Repository layout and run status

The committed tree does **not** include `requirements.txt`/`pyproject.toml`, a `smart_expense_tracker/` package, an `expenses/` application package, migrations, or the configured `templates/` and `static/` directories. This is significant: `manage.py` refers to `smart_expense_tracker.settings`; `settings.py` refers to `expenses.apps.ExpensesConfig` and `smart_expense_tracker.urls`; the root URL configuration includes `expenses.urls`; and views render paths such as `expenses/dashboard.html`. The settings also look for `static/css/style.css` and `static/js/main.js`, whereas `style.css` and `main.js` are at the repository root. Those expected modules and paths are absent from the checked-in tree.

Consequently, the usual Django start commands below describe the intended development workflow, but **the repository as committed is not runnable with those commands without first restoring/arranging the expected Django package, template, static, and migration structure**. No source files other than this README are changed by this documentation update. The project does not include a dependency lockfile, so the dependency installation command is a best-effort list of direct Python imports, not a project-pinned environment.

## Installation and setup

1. Clone the repository and enter its directory:

   ```bash
   git clone https://github.com/kishorerajas0609-svg/Smart-Expense-Tracker.git
   cd Smart-Expense-Tracker
   ```

2. Create and activate a virtual environment (Python 3.10+ is a practical baseline for modern Django; the repository does not declare a supported Python version):

   ```bash
   python -m venv .venv
   ```

   On macOS/Linux:

   ```bash
   source .venv/bin/activate
   ```

   On Windows PowerShell:

   ```powershell
   .venv\Scripts\Activate.ps1
   ```

3. Install the Python packages imported by the application. No dependency file is currently provided:

   ```bash
   python -m pip install Django reportlab
   ```

4. Before running Django, address the package/path mismatch described above: the project files must be available as the `smart_expense_tracker` project and `expenses` app, with templates in the configured template locations and assets at `static/css/style.css` and `static/js/main.js`. The current repository does not include a command or script to perform that setup.

## Run the application

Once the expected Django package and directory layout is in place, the standard local development commands are:

```bash
python manage.py migrate
python manage.py runserver
```

Then open <http://127.0.0.1:8000/>. Django's default admin route is `/admin/`; an administrator can be created with `python manage.py createsuperuser` after the project layout is corrected and migrations have run. These commands have not been verified against the current root-level checkout, which is missing the referenced project/app modules.

The `seed_data.py` file defines a Django management command, but it is currently at the repository root rather than in the required app command directory. After placing it in the appropriate Django command package and running migrations, it can be invoked using its command name as exposed by the installed command module. The expected command name is not configured by any checked-in directory structure, so no seed invocation is claimed here.

## Database

- **Engine:** SQLite (`django.db.backends.sqlite3`), as set in `settings.py`.
- **Configured location:** `BASE_DIR / 'db.sqlite3'`; `BASE_DIR` is calculated from the settings file location, so the effective path depends on the proper Django project placement.
- **Data model:** `Expense` belongs to Django's built-in `User` model through a foreign key. It stores description, decimal amount, category, date, optional notes, and timestamps. The model defines indexes on user/date and user/category.
- **Included file:** a `db.sqlite3` file is checked in at the repository root. Because of the missing project package layout, it cannot be confirmed from the committed configuration that this file is the database Django would open when run.
- **Schema setup:** use Django migrations (`python manage.py migrate`) after restoring the expected project/app structure. No migration files are present in the current tree.

## Tests

`tests.py` contains Django tests for keyword category prediction, authentication, user-level data isolation, expense validation and CRUD, filtering, and CSV/PDF exports. The test module imports `.models`, so it also requires the expected application package layout. After correcting that layout and installing dependencies, run:

```bash
python manage.py test
```

## Screenshots

No screenshot files or screenshot directory are included in the repository at this time. Add screenshots here when they are available.

## Future enhancements

These are suggestions, not features currently claimed as implemented:

- Add a dependency manifest and migrations so a fresh clone has a reproducible installation and database setup.
- Arrange the tracked code into a valid Django project/app structure and add automated checks for template and static-file paths.
- Add screenshots or a short setup demonstration.
- Move secrets and deployment-specific settings out of source, and document production deployment requirements.
- Expand automated test coverage for profile updates, passwords, custom date ranges, and report filter combinations.
- Consider optional configurable categories, budgets, or recurring transactions if those fit the project's intended scope.
