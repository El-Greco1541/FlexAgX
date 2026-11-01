"""Make unavailable ReShade FX/GPU toolchain a visible independent status."""
import importlib.util,json,shutil,platform,os
from pathlib import Path

def toolchain():
    tools={name:shutil.which(name) for name in ('reshadefx','glslangValidator','dxc','fxc','nvidia-smi','vulkaninfo')}
    reshade_compiler=tools['reshadefx']
    gpu_available=bool(tools['nvidia-smi'] or tools['vulkaninfo'])
    return {'status':'NOT_RUN' if not reshade_compiler else 'AVAILABLE_UNTESTED','reason':'No executable ReShade FX compiler found; neither GL shader validators nor HLSL compiler alone certify ReShade FX semantics' if not reshade_compiler else 'ReShade compiler executable discovered but automated invocation not established', 'tools':{name:('FOUND' if path else 'NOT_FOUND') for name,path in tools.items()},'gpu_runtime':'UNVERIFIED' if gpu_available else 'NOT_DETECTED','native_shader_compilation':'NOT_EXECUTED','native_effect_rendering':'NOT_EXECUTED','scope':'This probe does not attempt to claim FX compiler or GPU acceptance.'}

if __name__=='__main__':print(json.dumps(toolchain(),indent=2))
