from pathlib import Path
import sys
import pytest
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
from transmigration.adapters import ReferenceCPUAdapter,controller,contracts
from transmigration.glue import CorrectnessFirstGlue
@pytest.fixture
def make_engine(tmp_path):
    def make(persistent=False,ports=None):
        db=str(tmp_path/'session.sqlite3') if persistent else ':memory:'
        return CorrectnessFirstGlue(controller.SessionStore(db_path=db),ports or ReferenceCPUAdapter())
    return make
