"""Independent bounded reference oracles; never claim GPU pixel equivalence."""
import math

LOG_MIN=-12.47393
LOG_RANGE=16.499999
WHITE=0.98

def reference_hue(stage,a,b):
    chroma=math.hypot(a,b)
    edge={'source-hue':1e-4,'curved-hue':1e-6,'output-gamut':1e-6}[stage]
    guarded=(chroma<edge) if stage=='source-hue' else (chroma<=edge)
    return 0.0 if guarded else math.atan2(b,a),guarded

def histogram_source_model(image, width, height, frame_index):
    """Deterministic CPU *model* of P1's integer phase and bin logic, not FX execution.

    image is a row-major encoded RGB pixel list, values in [0,1].
    Returns 67 UInt32 counters. Work is bounded to width*height.
    """
    assert 1<=width<=64 and 1<=height<=64 and len(image)==width*height
    fc=frame_index & 0xffffffff
    hsh=(fc*747796405+2891336453)&0xffffffff
    ox=(hsh>>13)&1; oy=(hsh>>26)&1
    counts=[0]*67
    def decode(v):
        return v/12.92 if v<=0.04045 else ((min(1.0,max(0.0,(v+0.055)/1.055)))**2.4)
    for yy in range((height+1)//2):
        for xx in range((width+1)//2):
            x=xx*2+ox;y=yy*2+oy
            if x>=width or y>=height:continue
            counts[66]+=1
            rgb=[decode(float(c)) for c in image[y*width+x]]
            if max(rgb)<=0:continue
            Y=rgb[0]*.2126+rgb[1]*.7152+rgb[2]*.0722
            idx=min(63,max(0,int(math.floor((math.log2(max(Y,2**LOG_MIN))-LOG_MIN)*(64.0/LOG_RANGE)))))
            counts[idx]+=1;counts[64]+=1
            if Y>=WHITE:counts[65]+=1
    return counts

def lut_domain_index(u):
    """Manual LUT texel positions, independent boundary reference."""
    u=max(0.,min(1.1,float(u)))
    v=u*1023/1.1
    i0=int(v); i1=min(i0+1,1023)
    return i0,i1,v-i0
