from app.config.paths import DATA_DIR, LOGS_DIR, PROJECT_ROOT, TEMPLATES_DIR


def test_project_root_points_at_the_repo_root():

    assert (PROJECT_ROOT / "app").is_dir()
    assert (PROJECT_ROOT / "tests").is_dir()
    assert (PROJECT_ROOT / "requirements.txt").is_file()


def test_derived_dirs_are_anchored_under_project_root():

    assert DATA_DIR == PROJECT_ROOT / "data"
    assert LOGS_DIR == PROJECT_ROOT / "logs"
    assert TEMPLATES_DIR == PROJECT_ROOT / "app" / "web" / "templates"
