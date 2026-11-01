import base64,io
import numpy as np
from PIL import Image
from fastapi.testclient import TestClient
from services.gateway import app
from services.observer import app as observer

def test_invalid_png_rejected():
    result=TestClient(observer).post('/v1/observe',json={
        'image_png_base64':base64.b64encode(b'not-a-png').decode('ascii'),
        'frame_index':1})
    assert result.status_code==422

def test_gateway_settings_out_of_range_rejected():
    result=TestClient(app).post('/v1/frame',json={
        'image_png_base64':'aaaa','frame_index':1,'settings':{'ColorTemp':1}})
    assert result.status_code==422

def test_gateway_missing_required_frame_rejected():
    result=TestClient(app).post('/v1/frame',json={'session_id':'test'})
    assert result.status_code==422
