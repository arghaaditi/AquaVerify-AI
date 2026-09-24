from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
MODELS_DIR = ROOT / "models"
OUTPUTS_DIR = ROOT / "outputs"

FEATURES = (DATA_DIR / "model_features_v2.txt").read_text(encoding="utf-8").strip().splitlines()
QUALITY_FIELD = "overall_ecosystem_quality"
REQUIRED_FIELDS = FEATURES + [QUALITY_FIELD]
ENGINE_VERSION = "0.2.0"
RARITY_THRESHOLD = 0.05
