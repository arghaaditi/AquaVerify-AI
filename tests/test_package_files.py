from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_required_repository_files_exist():
    required = [
        ROOT / "app.py",
        ROOT / "README.md",
        ROOT / "requirements.txt",
        ROOT / "preflight.py",
        ROOT / ".streamlit" / "config.toml",
        ROOT / "src" / "engine.py",
        ROOT / "src" / "demo_presets.py",
        ROOT / "src" / "presentation.py",
        ROOT / "database" / "db.py",
        ROOT / "database" / "demo_data.py",
        ROOT / "models" / "IsolationForest.joblib",
        ROOT / "models" / "OneClassSVM.joblib",
        ROOT / "models" / "model_thresholds.json",
        ROOT / "data" / "reference_train.csv",
        ROOT / "data" / "conditional_rarity_table.csv",
        ROOT / "docs" / "DEMO_SCRIPT.md",
        ROOT / "docs" / "TESTING.md",
        ROOT / "docs" / "ARCHITECTURE.md",
    ]
    for path in required:
        assert path.exists(), path


def test_streamlit_is_declared():
    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8").lower()
    assert "streamlit" in requirements


def test_runtime_database_is_not_committed():
    assert not (ROOT / "database" / "aquaverify.db").exists()
