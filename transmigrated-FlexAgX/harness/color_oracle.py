"""CT-006 CPU reference only: signed Oklab conversion, post-mix chroma containment,
plus an explicit CT-007/F40 characterization of the 0%-strength encoding policy.
No claim of float32, GPU shader compiler, colorimetric or visual equivalence.
"""
import math

M1=((.4122214708,.5363325363,.0514459929),(.2119034982,.6806995451,.1073969566),(.0883024619,.2817188376,.6299787005))
M2=((.2104542553,.7936177850,-.0040720468),(1.9779984951,-2.4285922050,.4505937099),(.0259040371,.7827717662,-.8086757660))
INV=((4.0767416621,-3.3077115913,.2309699292),(-1.2684380046,2.6097574011,-.3413193965),(-.0041960863,-.7034186145,1.7076147010))

def mat_vec(rows,vec):return tuple(sum(a*b for a,b in zip(row,vec)) for row in rows)
def cuberoot(x):return math.copysign(abs(x)**(1./3.),x)
def to_lab(rgb):
    if len(rgb)!=3 or not all(math.isfinite(v) for v in rgb):raise ValueError('nonfinite or invalid rgb')
    return mat_vec(M2,tuple(cuberoot(x) for x in mat_vec(M1,rgb)))
def from_lab(lab):
    L,a,b=lab
    lp=L+.3963377774*a+.2158037573*b
    mp=L-.1055613458*a-.0638541728*b
    sp=L-.0894841775*a-1.2914855480*b
    return mat_vec(INV,(lp**3,mp**3,sp**3))
def ingamut(rgb):return all(0<=v<=1 for v in rgb)
def constrain_composite(rgb):
    """Same 12-step branch as candidate FX; returns original values when in gamut."""
    if len(rgb)!=3 or not all(math.isfinite(v) and -8<=v<=8 for v in rgb):raise ValueError('nonfinite or unreasonable composite')
    if ingamut(rgb):return tuple(rgb)
    L,a,b=to_lab(rgb)
    L=max(0.,min(1.,L));lo=0.;hi=1.
    for _ in range(12):
        mid=(lo+hi)*.5
        trial=from_lab((L,a*mid,b*mid))
        if ingamut(trial):lo=mid
        else:hi=mid
    return tuple(max(0.,min(1.,v)) for v in from_lab((L,a*lo,b*lo)))

def mixed(original,processed,strength):
    if not(0<=strength<=100):raise ValueError('strength')
    if any(not math.isfinite(v) for v in (*original,*processed)):raise ValueError('nonfinite inputs')
    w=strength/100.
    return tuple(a+(b-a)*w for a,b in zip(original,processed))

def encode(value,encoding):
    if not math.isfinite(value) or not 0<=value<=1:raise ValueError('encoded domain 0..1')
    if encoding=='srgb':return value*12.92 if value<=.0031308 else 1.055*value**(1/2.4)-.055
    if encoding=='gamma22':return value**(1/2.2)
    raise ValueError('unsupported encoding')

def decode(value,encoding):
    if not math.isfinite(value) or not 0<=value<=1:raise ValueError('encoded domain 0..1')
    if encoding=='srgb':return value/12.92 if value<=.04045 else ((value+.055)/1.055)**2.4
    if encoding=='gamma22':return value**2.2
    raise ValueError('unsupported encoding')

def bypass_or_encode(original_code, linear_after_mix, strength, output_encoding, debug=0):
    """F40: 0% is exact original coded value; other path chooses OutputEncoding."""
    if not(0<=strength<=100):raise ValueError('strength')
    if strength==0 and debug==0:return original_code
    return encode(linear_after_mix,output_encoding)
