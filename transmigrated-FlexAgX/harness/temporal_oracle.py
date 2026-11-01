"""CPU-only oracle for F18/F32 temporal marker. Never a GPU acceptance oracle."""
import math
MAGIC_A=17231.0
MAGIC_B=28531.0
UINT32=(1<<32)-1

def temporal_marker(frame: int):
    f=frame & UINT32
    return (MAGIC_A,MAGIC_B,float(f & 65535),float(f >> 16))

def normalized_reference(counts):
    if len(counts)!=64 or any(not isinstance(v,int) or v<0 for v in counts):
        raise ValueError('expect 64 nonnegative integral histogram counts')
    total=sum(counts)
    return [float(v)/float(total) if total else 0.0 for v in counts]

def temporal_valid(stamp,now,old0,old1):
    if len(stamp)!=4 or len(old0)!=4 or len(old1)!=4:return False
    if any(not math.isfinite(float(x)) for x in stamp):return False
    if tuple(stamp)!=temporal_marker((now-1)&UINT32):return False
    if any(not math.isfinite(float(x)) for x in (*old0,*old1)):return False
    if any(abs(x)>limit for x,limit in zip(old0,(32.,8.,1.,1.))):return False
    if any(abs(x)>limit for x,limit in zip(old1,(1.,1.,2.,1.))):return False
    if old1[1] not in (0.,1.):return False
    return True
