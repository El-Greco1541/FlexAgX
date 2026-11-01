"""CPU research port. Original source preserved in reference/FlexAgX_original.fx.

Preserves shader equations and pass order where practical. Differences: CPU float64
math, PNG quantization at API edge, scipy edge filters, no GPU texture samplers
or GPU render-target precision equivalence. Never claim bit-exact fidelity.
"""
from __future__ import annotations
import base64
import io
from functools import lru_cache
import numpy as np
from PIL import Image, ImageFile
from scipy.ndimage import uniform_filter
from .contracts import Observation, Settings, ToneResult

Image.MAX_IMAGE_PIXELS = 2_000_000
ImageFile.LOAD_TRUNCATED_IMAGES = False
MAX_PIXELS = 2_000_000
LOG_MIN = -12.47393
LOG_RANGE = 16.499999
UB = .05126
GREY = .18
LUMA = np.array([.2126, .7152, .0722])
INSET = np.array([[.842479062253094,.0423282422610123,.0423756549057051],
                  [.0784335999999992,.878468636469772,.0784336],
                  [.0792237451477643,.0791661274605434,.879142973793104]])
OUTSET = np.array([[1.19687900512017,-.0528968517574562,-.0529716355144438],
                   [-.0980208811401368,1.15190312990417,-.0980434501171241],
                   [-.0990297440797205,-.0989611768448433,1.15107367264116]])
RGB_TO_LMS = np.array([[.4122214708,.5363325363,.0514459929],
                       [.2119034982,.6806995451,.1073969566],
                       [.0883024619,.2817188376,.6299787005]])
LMS_TO_RGB = np.array([[4.0767416613,-3.3077115904,.2309699287],
                       [-1.2684380041,2.6097574007,-.3413193963],
                       [-.0041960865,-.7034186145,1.7076147009]])
WB_REF = np.array([1.0106792805,1.0017568775,1.0211812566])


def clamp(x, lo, hi): return np.clip(x, lo, hi)


def decode(x, encoding=0):
    x = np.asarray(x, dtype=np.float64)
    if encoding == 1: return np.power(np.maximum(x, 0), 2.2)
    return np.where(x <= .04045, x / 12.92, np.power(clamp((x+.055)/1.055, 0, 1), 2.4))


def encode(x, encoding=0):
    x = np.asarray(x, dtype=np.float64)
    if encoding == 1: return np.power(np.maximum(x, 0), 1/2.2)
    return np.where(x <= .0031308, 12.92*x, 1.055*np.power(np.maximum(x,0),1/2.4)-.055)


def polynomial(x):
    return ((((((15.5*x - 40.14)*x + 31.96)*x - 6.868)*x + .4298)*x + .1191)*x - .00232)

NW = float(max(polynomial(1.0), 0)**2.4)


def dn(s):
    s=np.asarray(s, dtype=np.float64)
    with np.errstate(divide="ignore", invalid="ignore"):
        xs=clamp((np.log2(np.maximum(s,1e-300))-LOG_MIN)/LOG_RANGE,0,1)
    out=np.power(np.maximum(polynomial(xs),0),2.4)/NW
    return np.where(s <= 0,0,out)


def native(u, gain): return dn(np.asarray(u)*gain)


def native_slope(u,gain):
    h=1e-5
    return (native(np.maximum(np.asarray(u)+h,0),gain)-native(np.maximum(np.asarray(u)-h,0),gain))/(2*h)


def hermite(x,x0,x1,y0,y1,m0,m1):
    dx=x1-x0; t=(np.asarray(x)-x0)/dx
    return ((2*t**3-3*t**2+1)*y0 +(t**3-2*t**2+t)*dx*m0
            +(-2*t**3+3*t**2)*y1+(t**3-t**2)*dx*m1)


def composed(u,gain,knee,shadow):
    u=np.asarray(u,dtype=np.float64)
    nu=native(u,gain)
    nb=float(native(UB,gain)); sec=nb/UB; db=float(native_slope(UB,gain))
    toe=hermite(u,0,UB,0,nb,min(1.0,3*sec),min(db,3*sec))
    nk=float(native(knee,gain)); sech=(1.0-nk)/max(1.0-knee,1e-6)
    shoulder=hermite(u,knee,1.0,nk,1.0,min(float(native_slope(knee,gain)),3*sech),0.0)
    x=np.where(u<UB,nu*(1-shadow/100)+toe*(shadow/100),np.where(u<=knee,nu,shoulder))
    return np.where(u<=0,0,np.where(u>=1,1,x))


def lut_sample(x,lut):
    lut=np.asarray(lut,dtype=np.float64)
    fi=clamp(np.asarray(x),0,1023)
    i0=np.asarray(fi,dtype=np.int64); i1=np.minimum(i0+1,1023)
    return lut[i0]*(1-(fi-i0))+lut[i1]*(fi-i0)


def curve_rgb(rgb,lut):
    a=np.asarray(rgb)@INSET.T
    w=INSET@np.ones(3)
    x=clamp(a/w,0,1.1)*(1023/1.1)
    q=lut_sample(x,lut)*w
    return np.maximum(q@OUTSET.T,0)


def validate_lut(lut,input_encoding=0,output_encoding=0):
    lut=np.asarray(lut)
    if not np.isfinite(lut).all() or np.any(lut<0) or np.any(lut>1.000001) or np.any(np.diff(lut)<-1e-6):
        return False
    gray=np.linspace(0,1,256)[:,None].repeat(3,axis=1)
    out=curve_rgb(decode(gray,input_encoding),lut)
    codes=np.rint(255*encode(clamp(out,0,1),output_encoding))
    return bool(np.isfinite(codes).all() and np.all(np.diff(codes,axis=0)>=0))


def make_lut(gain,knee,shadow,input_encoding=0,output_encoding=0):
    grid=1.1*np.arange(1024)/1023
    used_fallback=False; attempts=0; trial_knee=knee
    for attempt in range(4):
        attempts=attempt+1
        arr=composed(grid,gain,trial_knee,shadow)
        if validate_lut(arr,input_encoding,output_encoding): break
        if attempt<3: trial_knee=max(.4,trial_knee-.05)
        else:
            used_fallback=True
            arr=np.clip(dn(gain*grid)/max(float(dn(gain)),1e-6),0,1)
    verified=validate_lut(arr,input_encoding,output_encoding)
    if not verified:
        # Hard failure rather than publishing an unchecked numerical result.
        raise ValueError('LUT failed bounded retry and fallback validation')
    return ToneResult(lut=arr.tolist(),validation_passed=True,used_fallback=used_fallback,attempts=attempts,final_knee=float(trial_knee))


def source_phase(frame_index):
    hsh=((int(frame_index)&0xffffffff)*747796405+2891336453)&0xffffffff
    return ((hsh>>13)&1,(hsh>>26)&1)


def observe(rgb_encoded,frame_index,settings):
    ox,oy=source_phase(frame_index)
    samples=np.asarray(rgb_encoded)[oy::2,ox::2,:3].reshape(-1,3)
    sample_count=int(len(samples))
    linear=decode(samples,settings.InputEncoding)
    valid=np.max(linear,axis=1)>0
    y=linear@LUMA
    valid_y=y[valid]
    whites=int(np.count_nonzero(valid & (y>=.98)))
    bins=np.zeros(64,dtype=np.int64)
    if len(valid_y):
        with np.errstate(divide='ignore',invalid='ignore'):
            indices=np.floor((np.log2(np.maximum(valid_y,2**LOG_MIN))-LOG_MIN)*(64/LOG_RANGE)).astype(np.int64)
        bins=np.bincount(clamp(indices,0,63).astype(np.int64),minlength=64)
    return Observation(histogram=bins.astype(int).tolist(),valid_count=int(len(valid_y)),white_count=whites,
        sample_count=sample_count,e50=percentile(bins,.5),e90=percentile(bins,.9),phase_x=ox,phase_y=oy)


def percentile(bins,quantile):
    count=np.sum(bins)
    if count==0: return LOG_MIN
    target=float(count)*quantile; cumulative=0.0
    for i, c in enumerate(bins):
        old=cumulative; cumulative+=float(c)
        if cumulative>=target:
            fraction=clamp((target-old)/max(float(c),1),0,1)
            return float(LOG_MIN+(i+fraction)*(LOG_RANGE/64))
    return LOG_MIN


def oklab(rgb):
    p=np.asarray(rgb)@RGB_TO_LMS.T
    p=np.sign(p)*np.power(np.abs(p),1/3)
    return np.stack([p@np.array([.2104542553,.7936177850,-.0040720468]),
                    p@np.array([1.9779984951,-2.4285922050,.4505937099]),
                    p@np.array([.0259040371,.7827717662,-.8086757660])],axis=-1)


def from_oklab(lab):
    lab=np.asarray(lab)
    l,a,b=lab[...,0],lab[...,1],lab[...,2]
    tmp=np.stack([l+.3963377774*a+.2158037573*b,
                  l-.1055613458*a-.0638541728*b,
                  l-.0894841775*a-1.291485548*b],axis=-1)**3
    return tmp@LMS_TO_RGB.T


def hue_restore(src,curved,amount):
    src_lab=oklab(src)
    c=np.hypot(src_lab[...,1],src_lab[...,2])
    h_in=np.where(c<1e-4,0,np.arctan2(src_lab[...,2],src_lab[...,1]))
    lab=oklab(np.maximum(curved,0))
    h=np.arctan2(lab[...,2],lab[...,1])
    delta=(h_in-h+np.pi)%(2*np.pi)-np.pi
    s=clamp(c/.03,0,1); smooth=s*s*(3-2*s)
    theta=np.where(c<1e-4,0,delta*(amount/100)*smooth)
    cs=np.cos(theta); sn=np.sin(theta)
    a=lab[...,1]*cs-lab[...,2]*sn
    b=lab[...,1]*sn+lab[...,2]*cs
    return from_oklab(np.stack([lab[...,0],a,b],axis=-1))


def temp_white_rgb(temp):
    t=float(clamp(temp,1667,25000)); u=1000/t; u2=u*u; u3=u2*u
    x=(-.2661239*u3-.2343580*u2+.8776956*u+.179910) if t<4000 else (-3.0258469*u3+2.1070379*u2+.2226347*u+.240390)
    x2=x*x; x3=x2*x
    if t<2222: y=-1.1063814*x3-1.34811020*x2+2.18555832*x-.20219683
    elif t<4000: y=-.9549476*x3-1.37418593*x2+2.09137015*x-.16748867
    else: y=3.0817580*x3-5.87338670*x2+3.75112997*x-.37001483
    inv=1/max(y,1e-4); X=x*inv; Z=(1-x-y)*inv
    w=np.maximum([3.2406255*X-1.5372080-.4986286*Z,
                   -.9689307*X+1.8757561+.0415175*Z,
                   .0557101*X-.2040211+1.0569959*Z],0)
    return w/max(w@LUMA,1e-6)


@lru_cache(maxsize=256)
def temp_gain(temperature):
    return (RGB_TO_LMS@temp_white_rgb(temperature))/WB_REF


def white_balance(rgb,temperature):
    if float(temperature)==6500.0: return np.asarray(rgb)
    return ((np.asarray(rgb)@RGB_TO_LMS.T)*temp_gain(float(temperature)))@LMS_TO_RGB.T


def gamut_map(rgb,start):
    lab=oklab(rgb)
    L=np.minimum(lab[...,0],1)
    a,b=lab[...,1],lab[...,2]
    C=np.hypot(a,b); h=np.arctan2(b,a)
    ch,sh=np.cos(h),np.sin(h)
    lo=np.zeros_like(C); hi=np.full_like(C,.4)
    # Shader bisection is skipped for achromatic pixels. Keeping a deterministic
    # zero-valued CPU branch here does not assert GPU atan2(0,0) semantics.
    active=C>1e-6
    for _ in range(10):
        mid=(lo+hi)*.5
        trial=from_oklab(np.stack([L,mid*ch,mid*sh],axis=-1))
        good=np.all((trial>=-1e-4)&(trial<=1.0001),axis=-1)
        lo=np.where(active&good,mid,lo)
        hi=np.where(active&~good,mid,hi)
    Cmax=lo
    x=C/np.maximum(Cmax,1e-6); k=start
    t=np.maximum((x-k)/(1-k),0)
    yy=np.where(x>k,k+(1-k)*t/np.power(1+np.power(t,1.2),1/1.2),x)
    Cp=yy*Cmax
    return clamp(from_oklab(np.stack([L,Cp*ch,Cp*sh],axis=-1)),0,1)


def detail(rgb,amount):
    if amount<=0: return np.asarray(rgb)
    # P5/P6 RG16F render targets, approximated by float16 casts between passes.
    Y=np.asarray(rgb)@LUMA
    mean=uniform_filter(Y,size=5,mode='nearest')
    mean2=uniform_filter(Y*Y,size=5,mode='nearest')
    variance=np.maximum(mean2-mean*mean,0)
    mv=np.stack([mean,variance],axis=-1).astype(np.float16).astype(np.float64)
    a=mv[...,1]/(mv[...,1]+.001); b=(1-a)*mv[...,0]
    a_bar=uniform_filter(a,size=5,mode='nearest'); b_bar=uniform_filter(b,size=5,mode='nearest')
    q=np.stack([a_bar,b_bar],axis=-1).astype(np.float16).astype(np.float64)
    base=q[...,0]*Y+q[...,1]
    ratio=np.where(Y<=1e-6,1,np.power(np.maximum(Y/np.maximum(base,1e-4),0),amount/100))
    return rgb*clamp(ratio,.25,4)[...,None]


def dither(encoded,depth=8):
    h,w=encoded.shape[:2]; x,y=np.meshgrid(np.arange(w),np.arange(h))
    frac=lambda a: a-np.floor(a)
    noise=frac(52.9829189*frac(.06711056*x+.00583715*y))-.5
    factor=1023 if depth==10 else 255
    return clamp(encoded+noise[...,None]/factor,0,1)


def render_pixels(source_rgba,settings,lut,gain_ev=0):
    arr=np.asarray(source_rgba,dtype=np.float64)
    encoded_src=arr[...,:3]; alpha=arr[...,3:]
    if settings.OverallStrength<=0 and settings.DebugView==0: return arr.copy()
    src=decode(encoded_src,settings.InputEncoding)
    a=curve_rgb(src,lut)
    # RGBA16F intermediate approximated at pass boundaries
    a=a.astype(np.float16).astype(np.float64)
    b=hue_restore(src,a,settings.HueRestoration).astype(np.float16).astype(np.float64)
    d=detail(b,settings.LocalDetail).astype(np.float16).astype(np.float64)
    orig=white_balance(src,settings.ColorTemp)
    rgb=white_balance(np.maximum(d,0),settings.ColorTemp)
    mapped=gamut_map(rgb,settings.GamutRolloffStart)
    linear=orig*(1-settings.OverallStrength/100)+mapped*(settings.OverallStrength/100)
    if settings.DebugView==1:
        mask=(orig@LUMA)>=.98
        linear=np.where(mask[...,None],[1,0,1],linear)
    elif settings.DebugView==2:
        g=float(clamp((float(clamp(gain_ev,-2,2))+2)/4,0,1))
        linear=np.broadcast_to([g,g,g],linear.shape)
    result=encode(clamp(linear,0,1),settings.OutputEncoding)
    if settings.Dithering: result=dither(result)
    output=np.concatenate([clamp(result,0,1),alpha],axis=-1)
    if not np.isfinite(output).all():
        raise ValueError('non-finite renderer output; frame rejected')
    return output


def png_decode(b64):
    if len(b64)>20_000_000:
        raise ValueError('base64 payload exceeds input budget')
    raw=base64.b64decode(b64,validate=True)
    if len(raw)>15_000_000: raise ValueError('Encoded PNG exceeds 15 MB')
    with Image.open(io.BytesIO(raw)) as im:
        if im.format != 'PNG': raise ValueError('Only PNG images are accepted')
        if im.width*im.height>MAX_PIXELS: raise ValueError('Image exceeds 2,000,000 pixels')
        rgba=np.asarray(im.convert('RGBA'),dtype=np.float64)/255
    return rgba


def png_encode(rgba):
    pixels=np.asarray(rgba)
    if pixels.ndim!=3 or pixels.shape[2]!=4 or pixels.shape[0]<1 or pixels.shape[1]<1 or pixels.shape[0]*pixels.shape[1]>MAX_PIXELS:
        raise ValueError('output image dimensions outside bounded RGBA domain')
    if not np.isfinite(pixels).all():
        raise ValueError('non-finite pixels cannot be serialized')
    buf=io.BytesIO()
    data=np.uint8(np.rint(clamp(pixels,0,1)*255))
    Image.fromarray(data,'RGBA').save(buf,format='PNG')
    return base64.b64encode(buf.getvalue()).decode('ascii')
