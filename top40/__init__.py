"""JSE Top 40 three-cross-section clustering study."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUTS = ROOT / 'data/processed/Top40_Retrospective_Model_Inputs_v1.csv'
WORKBOOK = ROOT / 'data/source/Top40_PIT_Verification_v4.xlsx'
DATA_POLICY = ROOT / 'data/processed/Top40_Retrospective_Model_Method_v1.json'
CORPORATE_ACTIONS = ROOT / 'data/reference/corporate_actions.csv'
VOLUME_CORRECTIONS = ROOT / 'data/reference/volume_corrections.csv'
DUAL_LISTED_SHARES = ROOT / 'data/reference/dual_listed_shares.csv'
INDEX_CHANGES = ROOT / 'data/reference/index_changes.csv'
CONFIG = ROOT / 'configs/study.json'
