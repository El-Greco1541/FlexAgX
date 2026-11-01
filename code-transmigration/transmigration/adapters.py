"""Replaceable ports for source-equation CPU baseline; no added lookalike formulas."""
from __future__ import annotations
from typing import Protocol, Any
from .dependencies import import_cpu_core

compute, contracts, controller = import_cpu_core()

class ObserverPort(Protocol):
    def observe(self, rgba:Any, index:int, settings:Any)->Any: ...

class TonePort(Protocol):
    def build(self, control:Any, settings:Any)->Any: ...

class RendererPort(Protocol):
    def render(self, image:Any, settings:Any, lut:list[float], gain_ev:float)->Any: ...

class ImagePort(Protocol):
    def decode(self, png_base64:str)->Any: ...
    def encode(self, rgba:Any)->str: ...

class ReferenceCPUAdapter:
    """No remote state, side effects, or network calls in numerical ports."""
    def decode(self,png_base64:str):return compute.png_decode(png_base64)
    def encode(self,rgba)->str:return compute.png_encode(rgba)
    def observe(self,rgba,index:int,settings):return compute.observe(rgba[...,:3],index,settings)
    def build(self,control,settings):return compute.make_lut(control.gain,control.knee,
        settings.ShadowPreservation,settings.InputEncoding,settings.OutputEncoding)
    def render(self,image,settings,lut,gain_ev):return compute.render_pixels(image,settings,lut,gain_ev)
