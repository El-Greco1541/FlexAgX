import pytest
from pydantic import ValidationError
from flexagx.contracts import Settings,FrameRequest
from flexagx.compute import observe,source_phase
import numpy as np

@pytest.mark.parametrize('name,value', [('OverallStrength',-1),('ColorTemp',30000),('LocalDetail',80),('InputEncoding',4)])
def test_rejects_unsupported_settings(name,value):
    with pytest.raises(ValidationError): Settings(**{name:value})

def test_frame_rejects_invalid_session():
    with pytest.raises(ValidationError):
        FrameRequest(image_png_base64='aaaa',session_id='../escape',frame_index=0)

def test_odd_dimension_sample_counts_match_source():
    image=np.ones((7,5,3),dtype=float)
    counts=[]
    for frame in range(100):
        x,y=source_phase(frame)
        obs=observe(image,frame,Settings())
        expected=((5+1-x)//2)*((7+1-y)//2)
        assert obs.sample_count==expected
        counts.append(obs.sample_count)
    assert set(counts)=={6,8,9,12}
