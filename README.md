# SkillBridge

SkillBridge is a Django-based university project that compares a user's skills with the skills expected for a target job role and recommends resources for closing meaningful gaps.

## Planned architecture

The project is organized as layered components: a framework-independent matcher, gap-scoring layer, recommender, Django REST Framework API, and templates with Chart.js for visualizations. The analysis engine remains independent of Django so it can be tested and reused outside the web application.

## Setup

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
python webapp\manage.py migrate
python webapp\manage.py load_knowledge_base
pytest
python webapp\manage.py runserver
```

Set `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, and `DJANGO_ALLOWED_HOSTS` in the environment when running outside local development. Development defaults are intentionally provided for local setup.

## Phase 1 knowledge base

The domain model contains `Skill`, `JobRole`, `JobSkillRequirement`, `UserSkill`, and `LearningResource`. A role has many skills through requirements, each requirement storing a validated required level and importance. User skills can belong to an authenticated Django user or a free-text session, and resources are linked to skills with type, level, cost, URL, and notes.

Knowledge-base JSON is stored under `knowledge_base/`. `skills.json` contains canonical skills with `name`, `category`, and `description`. Each `knowledge_base/roles/<slug>.json` contains `title`, `slug`, `description`, and a `skills` array. Every array item names a skill exactly and contains `required_level`, `importance`, and one or more resources with `title`, `url`, `resource_type`, `level`, `is_free`, and `notes`.

After migrations, load or reload the fixtures with:

```powershell
python webapp/manage.py migrate
python webapp/manage.py load_knowledge_base
```

The loader is idempotent and can safely be run again. This knowledge base is a first draft and must be reviewed against real job postings and O*NET before it supports research conclusions or production recommendations.

## Gap scoring

The framework-independent scorer in `analyzer/gap_scoring.py` compares each role requirement with a user's skill level from 0 to 5. For each skill, `raw_gap = max(0, required_level - user_level)` and `weighted_gap = raw_gap * importance`. The overall gap score is `sum(weighted_gap) / sum(required_level * importance)`; the match percentage is `round((1 - overall_gap_score) * 100, 1)`. Missing skills count as level 0, and over-qualified skills receive no bonus.

```python
from analyzer.gap_scoring import calculate_gap, load_role

title, requirements = load_role("data-analyst")
report = calculate_gap(requirements, {"SQL": 4, "Python": 2}, title)
print(report.overall_match_percent)
print([gap.skill for gap in report.missing])
```

## Skill matching

The matcher in `analyzer/matching.py` uses Gensim Word2Vec trained from random initialization on the job descriptions in `data/job_dataset.csv`, sourced from Kaggle dataset "Job Descriptions 2025 - Tech & Non-Tech Roles"; the ML pipeline loads no pretrained weights. Each CSV job row contributes its title, semicolon-separated skills, responsibilities, and semicolon-separated keywords to one training document. The reproducible training, preprocessing, export, and evaluation workflow is the submission notebook [`notebooks/train_matcher_from_scratch.ipynb`](notebooks/train_matcher_from_scratch.ipynb).

The checked-in CSV has 1,068 job rows. Cleaning produces 74,081 word tokens and 1,740 distinct token types; the documented `min_count=2` yields 1,487 tokens by corpus frequency (the executed notebook should confirm the trained vocabulary).

Install `requirements.txt`, then run every notebook cell from the repository root. It saves `models/word2vec_scratch.model`, `models/skill_embeddings.json`, and evaluation records. Model and dataset files are ignored by Git. The application requires those generated model artifacts; the API singleton loads them once at Django startup.

Phrase embeddings average the vectors for known words and ignore out-of-vocabulary words. A phrase with no known words is rejected. Canonical skills with no in-vocabulary tokens are flagged as unavailable and omitted from ranking. This simple representation has no word order or contextual meaning. The notebook reports corpus and vocabulary sizes, training time, no-vector skills, a threshold sweep, full-fixture top-1 accuracy, and error examples. The historical pretrained baseline was 89.7% (52/58) on an earlier, smaller subset; compare it with the notebook's result on all 154 checked-in examples while noting the sample-size difference.

The existing labelled examples are in `tests/fixtures/matching_examples.json`. Run the evaluator after training with `python -m analyzer.eval_matching`. Threshold defaults to 0.5 and can be calibrated from the evaluation sweep in the notebook.

## Putting it together

The Phase 4 engine combines matching, gap scoring, and resource recommendations:

```python
from analyzer.engine import analyze

result = analyze(
    "data-analyst",
    {
        "wrote SQL queries": 3,
        "Python": 2,
        "I like pizza": 5,
    },
)

print(result.role_title)                    # Data Analyst
print(result.gap_report.overall_match_percent)
print(result.unmatched_inputs)              # ['I like pizza']
print([(item.priority_rank, item.skill) for item in result.recommendations])
```

`analyze()` leaves low-confidence inputs in `unmatched_inputs` rather than
guessing. If multiple phrases resolve to the same canonical skill, it uses the
higher user level. Recommendations include only missing or partial skills and
may have an empty resource list when the role fixture has no resources for that
skill.

## API

Phase 5 exposes two Django REST Framework endpoints. Roles are read directly
from the versioned JSON fixtures so API validation stays aligned with
`load_role()`.

- `GET /api/roles/` returns each role's `title`, `slug`, and `description`.
- `POST /api/skill-gap/` accepts `job_title`, a non-empty `skills` dictionary
  with levels from 0 to 5, and optional positive `top_n`.

Example request:

```json
{"job_title":"data-analyst","skills":{"Python":3,"wrote SQL queries":4,"I like pizza":5},"top_n":3}
```

The response includes `role_title`, `overall_gap_score`,
`overall_match_percent`, `skill_gaps`, ranked `recommendations`, and
`unmatched_inputs`:

```json
{"role_title":"Data Analyst","overall_gap_score":0.42,"overall_match_percent":58.0,"skill_gaps":[{"skill":"Statistics","required_level":4,"user_level":0,"weighted_gap":3.52,"status":"missing"}],"recommendations":[{"skill":"Statistics","priority_rank":1,"resources":[]}],"unmatched_inputs":["I like pizza"]}
```

Run the development server and try the endpoints with curl or httpie:

```powershell
python webapp\manage.py runserver
curl http://127.0.0.1:8000/api/roles/
curl -X POST http://127.0.0.1:8000/api/skill-gap/ -H "Content-Type: application/json" -d '{"job_title":"data-analyst","skills":{"Python":3,"SQL":4}}'
```

The Word2Vec matcher and skill vectors are initialized once when the API app starts and reused by every request in that server process.

## Frontend

Phase 6 adds the SkillBridge frontend at `/`: “See exactly what's between you
and your next role.” It renders the five loaded job roles server-side, accepts
repeatable skill and level rows, and submits the form to `POST /api/skill-gap/`
without a page reload. Results include a Chart.js comparison of required versus
user levels, the overall match percentage, unmatched inputs, and ranked resource
links.

Each skill row uses a labelled level selector: Beginner maps to 1, Intermediate
to 3, Advanced to 4, and Expert to 5. Leaving a level unselected omits that skill
from the request; omitted skills continue to count as level 0 (missing) in the
existing scoring logic. The frontend maps the selected option to an integer, so
the API payload remains `skills: {"skill name": 0-5}`.

The visual direction pairs Fraunces headings with Karla body text: Fraunces
brings an editorial warmth to the roadmap, while Karla keeps form controls and
supporting copy clear. Olive `#596B3D` anchors a warm cream `#F7F5ED` canvas and
`#2B2A25` text; forest `#3F512B`, rust `#A34F3E`, and amber `#87651F` carry
emphasis and skill status. The responsive layout uses restrained borders and
varied alignment. Vanilla JavaScript adds an eased match count-up, staggered
recommendation entrance, animated chart bars, smooth scrolling to results, and
an understated loading track. CSS and JavaScript honor `prefers-reduced-motion`.
The frontend remains framework-free and has no npm dependencies. It can be
served by Django on Vercel or built as a standalone static site for Render.

Chart.js is loaded from a CDN. Start the server with
`python webapp/manage.py runserver`, then open
`http://127.0.0.1:8000/`. When served by Django, the API base URL defaults to
the same origin. The Render static build sets a separate API base URL and loads
job roles from the API.

## Deploying to Vercel

The root-level `manage.py` lets Vercel detect this Django project. Push the
repository to GitHub, import it in Vercel, and keep the project root set to the
repository root. Vercel detects Python dependencies from `requirements.txt`.

Add these Environment Variables in Vercel for Production (and Preview if you
deploy preview branches):

- `DJANGO_SECRET_KEY`: a long, random secret.
- `DJANGO_DEBUG`: `False`.
- `DJANGO_ALLOWED_HOSTS`: `.vercel.app` plus any custom domain, comma-separated.
- `DATABASE_URL`: a persistent PostgreSQL connection URL for signup, login,
  sessions, and other database-backed features.

Without `DATABASE_URL`, local development uses SQLite. Vercel function
filesystems are temporary, so signup and login require a persistent PostgreSQL
database configured through `DATABASE_URL`.

The app also requires `models/word2vec_scratch.model` and
`models/skill_embeddings.json`. These generated artifacts are included in Git
so the Vercel function can load the matcher.

The analyzer reads role data from JSON fixtures, so its core pages and endpoints
do not need database migrations. Signup, login, sessions, and the admin do need
a persistent PostgreSQL database; SQLite on Vercel is temporary and is not
shared reliably across serverless instances.

## Deploying the frontend to Render

The optional Render Static Site redirects visitors to the Django app configured
by `SKILLBRIDGE_API_URL` (default:
`https://ai-skill-gap-analyzer-five.vercel.app`). This keeps the landing page,
login session, CSRF cookie, and analyzer API on the same origin. Set
`SKILLBRIDGE_API_URL` to your Django app's public origin if it differs from the
default. The Django app serves the actual website at `/`.

After configuring `DATABASE_URL`, apply migrations against the production
database before using signup or login:

```powershell
$env:DATABASE_URL = "<your PostgreSQL connection URL>"
python manage.py migrate
```

Keep the connection URL private and set the same value in Vercel's Production
environment variables. The analyzer's JSON role fixtures do not need to be
loaded into the database.

You can also inspect Vercel's current [Django deployment guide](https://vercel.com/templates/backend/django-hello-world).

## Project status

- Phase 0: repository and Django project setup complete.
- Phase 1: domain models, JSON knowledge base, loader, and tests complete.
- Phase 2: framework-independent gap scoring, validation, role loading, tests, and documentation complete.
- Phase 3: from-scratch Word2Vec skill matching, reproducible training notebook, reusable labelled evaluation data, evaluation harness, and integration tests complete once notebook artifacts have been generated.
- Phase 5: recommendations and Django REST API endpoints are complete.
- Phase 6: minimal template frontend and Chart.js visualization are complete.
