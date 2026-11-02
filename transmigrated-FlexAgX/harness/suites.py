"""Deterministic, seeded effect-oriented suites. Runtime FX execution is NOT supplied."""
import argparse, ast, hashlib, json, math, random, re, sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient
from correction_api.api import app
from correction_api.models import HueRequest, HistogramRequest
from correction_api.modules import safe_hue, clear_and_accumulate
from .fixtures import reference_hue,histogram_source_model,lut_domain_index
from .source_audit import check_corrections

ROOT=Path(__file__).resolve().parents[1]
REFERENCE_SHA='e744bdb7c410039f6835485c023f242ea399de14b09b3fd13657c02166d06e4d'
CANDIDATE_SHA='2700deed3c2ff76b439e2efa70d2c41f7b94cccd5efb4123afbd3623127960ec'

def checked(data, phase, detail, cases):
    assert data, f'{phase}: {detail}'
    cases.append(detail)

def check_no_null(value):
    if value is None:raise AssertionError('JSON null emitted')
    if isinstance(value,float) and not math.isfinite(value):raise AssertionError('nonfinite JSON emitted')
    if isinstance(value,dict):
        for v in value.values():check_no_null(v)
    if isinstance(value,list):
        for v in value:check_no_null(v)

def passes(text):
    return re.findall(r'\bpass (FlexAgX_\w+)\s*\{',text)

def source_suite(seed, frames):
    cases=[]
    reference=(ROOT/'reference/FlexAgX_1.2.fx').read_bytes()
    candidate=(ROOT/'shader/FlexAgX_transmigrated.fx').read_bytes()
    checked(hashlib.sha256(reference).hexdigest()==REFERENCE_SHA,'source','original SHA-256 matches upstream',cases)
    checked(hashlib.sha256(candidate).hexdigest()==CANDIDATE_SHA,'source','candidate SHA-256 unchanged',cases)
    checked(check_corrections(candidate.decode(),reference.decode())==[],'source','structural pass and guarded-HLSL audit passes',cases)
    old=passes(reference.decode());new=passes(candidate.decode())
    checked(len(old)==8 and len(new)==9 and new[1:]==old,'source','exact original eight pass names/order retained',cases)
    checked(new[0]=='FlexAgX_ClearHistogramPass','source','P0 histogram preclear ordered first',cases)
    text=candidate.decode()
    checked(re.search(r'\[numthreads\(128,\s*1,\s*1\)\]\s*void FlexAgX_ClearHistogram\(',text),'source','histogram clear launch spans 128 lanes',cases)
    checked('if (id.x < 67u)' in text and 'tex2Dstore(FA_HistStorage, int2((int)id.x, 0), 0u)' in text,'source','67 histogram slots covered by preclear',cases)
    checked(text.count('ComputeShader = FlexAgX_ClearHistogram;')==1,'source','clear pass bound to correct compute function',cases)
    checked(text.count('h = atan2(lab.z, lab.y)')==1 and text.count('h = atan2(b, a)')==1,'source','guarded hue-angle call sites intact',cases)
    checked('if (inputChroma >= 1.0e-4)' in text and 'if (curvedChroma > 1.0e-6)' in text and 'if (C > 1.0e-6)' in text,'source','three origin guards match intended boundaries',cases)
    checked('GroupMemoryBarrierWithGroupSync' not in text and 'barrier();' in text,'source','compute synchronization uses explicit shader barriers',cases)
    checked('FA_HistPrevStorage' in text and 'FA_StateStorage' in text,'source','state and histogram reads guarded by temporal initialization',cases)
    checked('if (OverallStrength <= 0.0 && DebugView == 0)' in text,'source','exact-bypass code path exists',cases)
    checked(not re.search(r'\bwhile\s*\(',text),'source','no shader while loops',cases)
    checked('for (int i = 0; i < 10; ++i)' in text,'source','chroma bisection loop explicitly limited',cases)
    checked('if (C > 1.0e-6)' in text[text.index('float4 FlexAgX_OutputPS'):],'source','gamut chroma bisection guarded at origin',cases)
    checked(re.search(r'\btex2Dfetch\(FA_StateStorage',text) and re.search(r'\btex2Dfetch\(FA_HistPrevStorage',text),'source','persistent resource reads are tracked as open risk',cases)
    checked('FA_ColdStart = valid ? 0 : 1;' in text,'source','cold-start marker controls retained-state reads',cases)
    checked('FA_PrevSh[lane] = currentNorm;' in text,'source','cold-start scene reference uses current histogram',cases)
    checked('tex2Dstore(FA_TemporalBootStorage' in text,'source','temporal marker written after successful state/histogram stores',cases)
    return cases

def temporal_suite(seed,frames):
    """Deterministic marker model and targeted poison/fault cases, NOT GPU execution."""
    from .temporal_oracle import temporal_marker, temporal_valid, normalized_reference
    cases=[]; rng=random.Random(seed ^ 0xB007)
    old0=(-5.0,0.0,0.5,0.0)
    old1=(0.2,1.0,0.1,0.3)
    for i in range(2200):
        now=rng.randrange(0,1<<32)
        marker=temporal_marker((now-1)&0xffffffff)
        checked(temporal_valid(marker,now,old0,old1),'temporal',f'valid consecutive {i}',cases)
        bad=list(marker); bad[i%4]+=1
        checked(not temporal_valid(bad,now,old0,old1),'temporal',f'invalid marker field {i}',cases)
        wrong=(now-rng.randrange(2,20000))&0xffffffff
        checked(not temporal_valid(temporal_marker(wrong),now,old0,old1),'temporal',f'nonconsecutive frame {i}',cases)
    # Special-case frame wraparound, per-channel NaN, Inf, oversized entries.
    checked(temporal_valid(temporal_marker(0xffffffff),0,old0,old1),'temporal','u32 wrap accepted',cases)
    checked(not temporal_valid(temporal_marker(0),0,old0,old1),'temporal','framecount reset rejected',cases)
    for i,value in enumerate((float('nan'),float('inf'),-float('inf'),1000000.0)):
        c=list(old0);c[i]=value
        checked(not temporal_valid(temporal_marker(4),5,c,old1),'temporal',f'corrupt old0 {i}',cases)
    for i,value in enumerate((float('nan'),float('inf'),-float('inf'),1000000.0)):
        c=list(old1);c[i]=value
        checked(not temporal_valid(temporal_marker(4),5,old0,c),'temporal',f'corrupt old1 {i}',cases)
    for i in range(1500):
        bins=[rng.randrange(0,20000) for _ in range(64)]
        ref=normalized_reference(bins)
        checked(len(ref)==64 and all(math.isfinite(z) and 0<=z<=1 for z in ref)
                and abs(sum(ref)-1.0)<1e-12,'temporal',f'cold hist normalized {i}',cases)
    checked(normalized_reference([0]*64)==[0.0]*64,'temporal','zero-count frame baseline',cases)
    return cases

def hue_suite(seed,frames):
    cases=[]; rng=random.Random(seed^0xF38)
    checked(len(reference_hue('output-gamut',0.,0.))==2,'hue','oracle output initialized',cases)
    values=[0.,1e-12,1e-7,1e-6,9.999e-5,1e-4,1.001e-4,1.,8.]
    for stage in ('source-hue','curved-hue','output-gamut'):
        for a in values:
            for b in values:
                for sign in (-1,1):
                    q=HueRequest(stage=stage,a=float(a),b=float(b)*sign)
                    result=safe_hue(q); theta,guard=reference_hue(stage,q.a,q.b)
                    checked(result.guarded==guard and abs(result.angle_rad-theta)<1e-12,'hue',f'{stage} boundary {a}/{b}/{sign}',cases)
    for i in range(2500):
        a=rng.uniform(-8,8);b=rng.uniform(-8,8)
        stage=('source-hue','curved-hue','output-gamut')[i%3]
        h=safe_hue(HueRequest(stage=stage,a=a,b=b));expected,guard=reference_hue(stage,a,b)
        checked(h.guarded==guard and math.isfinite(h.angle_rad) and abs(h.angle_rad-expected)<1e-12,'hue',f'angle oracle {i}',cases)
    for i in range(1000):
        a,b=rng.uniform(-4,4),rng.uniform(-4,4)
        h=safe_hue(HueRequest(stage='output-gamut',a=a,b=b))
        if h.guarded: continue
        k=rng.uniform(1.1,1.9)
        if abs(a*k)>8 or abs(b*k)>8:continue
        h2=safe_hue(HueRequest(stage='output-gamut',a=a*k,b=b*k))
        checked(not h2.guarded and abs(h.angle_rad-h2.angle_rad)<1e-12,'hue',f'positive scale invariance {i}',cases)
    return cases

def histogram_suite(seed,frames):
    cases=[]; rng=random.Random(seed^0xF41)
    for i in range(1200):
        bins=[rng.randrange(0,70) for _ in range(64)]; valid=sum(bins)
        white=rng.randrange(valid+1); samples=valid+rng.randrange(0,100)
        q=HistogramRequest(bins=bins,valid_count=valid,white_count=white,sample_count=samples)
        result=clear_and_accumulate(q).counters
        checked(len(result)==67 and result[:64]==bins and result[64:]==[valid,white,samples],'histogram',f'counts {i}',cases)
    for i in range(500):
        w=rng.randrange(1,33);h=rng.randrange(1,33)
        colors=[(0.,0.,0.),(1.,1.,1.),(.5,.5,.5),(.01,.02,.05),(.98,.99,1.),(.1,.8,.15)]
        image=[colors[rng.randrange(len(colors))] for _ in range(w*h)]
        f=rng.randrange(0,2**32)
        a=histogram_source_model(image,w,h,f)
        checked(sum(a[:64])==a[64] and 0<=a[65]<=a[64]<=a[66]<=((w+1)//2)*((h+1)//2),'histogram',f'image oracle {i}',cases)
        b=histogram_source_model(image,w,h,f+(1<<32))
        checked(b==a,'histogram',f'uint32 phase wrap {i}',cases)
    for w in (1,2,3,5,16,17,31,64):
        for h in (1,2,3,7,32):
            empty=[(0.,0.,0.)]*(w*h);white=[(1.,1.,1.)]*(w*h)
            for f in range(8):
                black=histogram_source_model(empty,w,h,f); bright=histogram_source_model(white,w,h,f)
                checked(black[64]==0 and black[65]==0 and black[66]==bright[66] and bright[64]==bright[65],'histogram',f'black/white {w}x{h} f{f}',cases)
    return cases

def interface_suite(seed,frames):
    cases=[];rng=random.Random(seed^0xAA)
    with TestClient(app) as client:
        for name in ('/health','/v1/capabilities'):
            r=client.get(name);check_no_null(r.json());checked(r.status_code==200,'interface',f'{name} probe',cases)
        valid={'stage':'output-gamut','a':0.0,'b':0.0}
        for i in range(650):
            obj=dict(valid)
            choice=i%13
            if choice==0:obj['a']=None
            elif choice==1:obj['a']='invalid'
            elif choice==2:obj['a']=True
            elif choice==3:obj['a']=1000.0
            elif choice==4:obj['a']=-1000.0
            elif choice==5:obj['stage']='not-a-stage'
            elif choice==6:obj['extra']=str(i)
            elif choice==7:obj.pop('b')
            elif choice==8:obj['b']={}
            elif choice==9:obj['a']=[1,2]
            elif choice==10:obj['a']=-1e100
            elif choice==11:obj['a']=1e-12
            elif choice==12:obj['b']=rng.uniform(-8,8)
            r=client.post('/v1/correction/hue',json=obj)
            check_no_null(r.json())
            expected=200 if choice in (11,12) else 422
            checked(r.status_code==expected,'interface',f'hue invalid/valid {i}',cases)
        for token in ('NaN','Infinity','-Infinity','1e10000'):
            r=client.post('/v1/correction/hue',content='{"stage":"output-gamut","a":'+token+',"b":0.0}',headers={'content-type':'application/json'})
            checked(r.status_code==422 and r.json()['sentinel']['fallback']=='NO_MUTATION','interface',f'nonfinite token {token}',cases)
        req={'bins':[0]*64,'valid_count':0,'white_count':0,'sample_count':0}
        for i in range(450):
            q={**req,'bins':req['bins'].copy()}
            choice=i%9
            if choice==0:q['bins']=[0]*63
            elif choice==1:q['bins']=[0]*65
            elif choice==2:q['bins'][0]=1
            elif choice==3:q['bins'][0]=-1
            elif choice==4:q['bins'][0]=True
            elif choice==5:q['white_count']=1
            elif choice==6:q['sample_count']=-1
            elif choice==7:q['bins'][0]=2000001
            elif choice==8:q['bins'][0]=1;q['valid_count']=1;q['sample_count']=1
            r=client.post('/v1/correction/histogram',json=q)
            check_no_null(r.json());expected=200 if choice==8 else 422
            checked(r.status_code==expected,'interface',f'histogram payload {i}',cases)
        for i in range(75):
            r=client.post('/v1/correction/hue',content=b'{bad-json',headers={'content-type':'application/json'})
            checked(r.status_code==422 and 'null' not in r.text.lower(),'interface',f'invalid JSON {i}',cases)
    return cases

def metamorphic_suite(seed,frames):
    cases=[];rng=random.Random(seed^0xABCD)
    for i in range(1200):
        u=rng.uniform(-10,10);k0,k1,t=lut_domain_index(u)
        checked(0<=k0<=k1<1024 and 0<=t<=1,'meta',f'LUT index bounds {i}',cases)
    for i in range(900):
        a,b=rng.uniform(-7,7),rng.uniform(-7,7)
        theta,guard=reference_hue('output-gamut',a,b)
        reflected,other=reference_hue('output-gamut',a,-b)
        checked(guard==other and abs(theta+reflected)<1e-12,'meta',f'polar reflect {i}',cases)
    for i in range(450):
        a=[rng.randrange(0,50) for _ in range(64)];b=[rng.randrange(0,50) for _ in range(64)]
        va=sum(a);vb=sum(b)
        result=clear_and_accumulate(HistogramRequest(bins=[x+y for x,y in zip(a,b)],valid_count=va+vb,white_count=0,sample_count=va+vb)).counters
        checked(result[:64]==[x+y for x,y in zip(a,b)] and result[64]==va+vb,'meta',f'additive histogram {i}',cases)
    return cases

def torture_suite(seed,frames):
    cases=[];rng=random.Random(seed^0xBABE)
    image=[];w=31;h=27
    palette=[(0.,0.,0.),(1.,1.,1.),(.25,.25,.25),(.99,.5,.01),(.01,.88,.3),(.01,.01,.02)]
    for i in range(w*h): image.append(palette[rng.randrange(len(palette))])
    prev=None
    for f in range(frames):
        if f%37==0:
            v=palette[rng.randrange(len(palette))]
            image=[v for _ in range(w*h)]
        if f%19==0:
            idx=rng.randrange(w*h);image[idx]=palette[rng.randrange(len(palette))]
        counters=histogram_source_model(image,w,h,f)
        req=HistogramRequest(bins=counters[:64],valid_count=counters[64],white_count=counters[65],sample_count=counters[66])
        out=clear_and_accumulate(req).counters
        checked(out==counters,'torture',f'frame {f}',cases)
        if prev is not None and f%37==1:
            checked(all(isinstance(k,int) for k in out),'torture',f'phase restored {f}',cases)
        prev=out
    return cases


def adaptation_suite(seed,frames):
    """CT-004 numerical and source-witness checks. Not GPU or timing certification."""
    from .adaptation_oracle import step_key, legacy_key_step, scene_cut_probe
    cases=[]; rng=random.Random(seed ^ 0xF23F24)
    # Regression reproduction: legacy drift inside the UI deadband.
    before=legacy_key_step(-4.,1.5,-3.98,16.667)
    after=step_key(-4.,1.5,-3.98,16.667)
    checked(before.key != -4. and after.key == -4. and after.velocity == 0., 'adaptation','legacy drift removed',cases)
    checked(step_key(-4.,-2.,-4.,16.667,deadband=0.).key == -4., 'adaptation','exact target neutral when deadband zero',cases)
    for i in range(2400):
        x=rng.uniform(-14,6); v=rng.uniform(-6,6);band=rng.uniform(0,.1)
        target=x+rng.uniform(-band,band) if band else x
        dt=rng.uniform(0,260)
        out=step_key(x,v,target,dt,deadband=band)
        checked(out.settled and out.key == x and out.velocity==0.,'adaptation',f'neutral deadband {i}',cases)
    for i in range(2400):
        x=rng.uniform(-13,5);v=rng.uniform(-3,3)
        band=rng.uniform(0,.1);target=x+rng.choice([-1,1])*rng.uniform(band+.05,.7)
        dt=rng.uniform(1,260);bright=rng.uniform(.1,3);dark=rng.uniform(.1,5);rate=rng.uniform(.5,6)
        out=step_key(x,v,target,dt,band,bright,dark,rate)
        old=legacy_key_step(x,v,target,dt,band,bright,dark,rate)
        checked(not out.settled and abs(out.key-old.key)<1e-12 and abs(out.velocity-old.velocity)<1e-12,'adaptation',f'unchanged outside deadband {i}',cases)
        checked(abs(out.velocity)<=rate+1e-12,'adaptation',f'velocity bounded {i}',cases)
    for i in range(400):
        # Diagnostic only: current shader requires sustained histogram change.
        threshold=.1; dt=rng.uniform(.001,.22);sensitivity=rng.uniform(.1,.6)
        fired,retained,advanced=scene_cut_probe(sensitivity+.01,sensitivity,0,dt*1000)
        checked(fired == (min(.25,max(.001,dt))>=threshold) and (advanced==fired),'adaptation',f'existing scene-cut clock {i}',cases)
    return cases


def scene_cut_suite(seed,frames):
    """CT-005: two-observation confirmation, baseline hold, F36 unchanged."""
    from .scene_cut_oracle import cut_step, old_cut_step, auto_strength_zero_contract
    cases=[]; rng=random.Random(seed ^ 0xF2905)
    # A single 100..250ms frame would have confirmed in v0.4.
    for ms in (100,101,150,200,250,500,1000):
        before=old_cut_step(.8,.35,0.,ms,key=-5.,target=-1.,velocity=.4)
        after=cut_step(.8,.35,0.,ms,key=-5.,target=-1.,velocity=.4)
        checked(before.fired and not after.fired and not after.update_reference and after.seconds>0,'scene_cut',f'single slow frame suppressed {ms}',cases)
        follow=cut_step(.8,.35,after.seconds,16.667,key=-5.,target=-1.,velocity=.4)
        checked(follow.fired and follow.update_reference and follow.seconds==0 and follow.velocity==0,'scene_cut',f'confirmed second observation {ms}',cases)
    checked(not cut_step(.8,.35,0,99.).fired,'scene_cut','subthreshold first frame',cases)
    for i in range(1800):
        ms=rng.uniform(1,1000);sensitivity=rng.uniform(.1,.6)
        first=cut_step(sensitivity+.01,sensitivity,0.,ms)
        checked(not first.fired and not first.update_reference and first.seconds==min(.25,max(.001,ms/1000)),'scene_cut',f'new candidate never fires {i}',cases)
        second=cut_step(sensitivity+.01,sensitivity,first.seconds,ms)
        checked(second.fired == (first.seconds+min(.25,max(.001,ms/1000))>=.1) and not (second.fired and second.seconds!=0), 'scene_cut',f'consecutive persistent {i}',cases)
        stop=cut_step(sensitivity,sensitivity,first.seconds,ms)
        checked(not stop.fired and stop.seconds==0 and stop.update_reference,'scene_cut',f'stable interruption resets {i}',cases)
    for i in range(2400):
        distance=rng.uniform(0,1);sensitivity=rng.uniform(.1,.6)
        elapsed=rng.uniform(.001,.5);ms=rng.uniform(1,250)
        key=rng.uniform(-14,6);target=rng.uniform(-14,6);v=rng.uniform(-3,3);rate=rng.uniform(.5,6)
        before=old_cut_step(distance,sensitivity,elapsed,ms,key=key,target=target,velocity=v,max_rate=rate)
        after=cut_step(distance,sensitivity,elapsed,ms,key=key,target=target,velocity=v,max_rate=rate)
        checked(before==after,'scene_cut',f'unchanged prior-candidate/stable {i}',cases)
        checked(abs(after.key_delta)<=.5*rate+1e-12 and (not after.fired or after.update_reference),'scene_cut',f'bounded correction {i}',cases)
    for i in range(1200):
        # Frame sequences including one-frame spikes, stalled frames and reverts.
        sensitivity=rng.uniform(.1,.6);sequence=[rng.choice([0.,sensitivity+.05]) for _ in range(12)]
        elapsed=0.
        for j,D in enumerate(sequence):
            prior=elapsed
            out=cut_step(D,sensitivity,elapsed,rng.uniform(5,400))
            checked(not out.fired or (prior>0 and D>sensitivity),'scene_cut',f'prior discrepant witness {i}.{j}',cases)
            elapsed=out.seconds
    for i in range(1100):
        manual=rng.uniform(-2,2);old_ev=rng.uniform(-3,3)
        result=auto_strength_zero_contract(manual,old_ev,tracker_advanced=bool(i%2))
        checked(result['applied_auto_ev']==0 and result['total_gain_ev']==manual and result['tracker_advanced']==bool(i%2),'scene_cut',f'F36 unchanged contribution {i}',cases)
    return cases

def gamut_suite(seed, frames):
    """CT-006 F39 post-blend chroma containment; CT-007 F40 policy witnesses.

    A CPU mathematical oracle only. Not a GPU rendering or FX compilation test.
    """
    from .color_oracle import (constrain_composite, to_lab, ingamut, mixed,
                               encode, decode, bypass_or_encode)
    import math
    cases=[];rng=random.Random(seed ^ 0xF3940)
    for i in range(2100):
        c=tuple(rng.random() for _ in range(3))
        checked(constrain_composite(c)==c,'gamut',f'in gamut identity {i}',cases)
    forced=0;hue_verified=0
    for i in range(2600):
        orig=tuple(rng.uniform(-.3,2.2) for _ in range(3))
        processed=tuple(rng.uniform(.02,.9) for _ in range(3))
        strength=rng.uniform(.001,99.9)
        unguarded=mixed(orig,processed,strength)
        result=constrain_composite(unguarded)
        checked(ingamut(result),'gamut',f'bounded postblend {i}',cases)
        if ingamut(unguarded):
            checked(result==unguarded,'gamut',f'unchanged already in gamut {i}',cases)
        else:
            forced+=1
            L,a,b=to_lab(unguarded)
            if .05<L<.95 and math.hypot(a,b)>1e-4:
                _,aa,bb=to_lab(result)
                n=math.hypot(a,b)*math.hypot(aa,bb)
                if n>1e-8:
                    checked((a*aa+b*bb)/n>.999,'gamut',f'hue direction preserved {i}',cases)
                    hue_verified+=1
    checked(forced>100 and hue_verified>100,'gamut','out gamut and hue witnesses exercised',cases)
    for i in range(900):
        code=rng.uniform(.01,.99)
        lin=decode(code,'srgb')
        checked(bypass_or_encode(code,lin,0,'gamma22')==code,'gamut',f'exact zero strength bypass {i}',cases)
        checked(abs(bypass_or_encode(code,lin,.0001,'gamma22')-code)>1e-6,'gamut',f'cross encoding jump disclosed {i}',cases)
        checked(abs(bypass_or_encode(code,lin,.0001,'srgb')-code)<1e-6,'gamut',f'matching encoding continuity {i}',cases)
    return cases

SUITES={'gamut':gamut_suite,'scene_cut':scene_cut_suite,'adaptation':adaptation_suite,'temporal':temporal_suite,'source':source_suite,'hue':hue_suite,'histogram':histogram_suite,'interface':interface_suite,'metamorphic':metamorphic_suite,'torture':torture_suite}

def main():
    p=argparse.ArgumentParser();p.add_argument('phase',choices=SUITES);p.add_argument('--seed',type=int,required=True);p.add_argument('--frames',type=int,default=1000);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    if not (0<=args.seed<=2**63-1 and 1<=args.frames<=2000):p.error('seed or frames out of bounds')
    out={'phase':args.phase,'seed':args.seed,'frames':args.frames,'status':'FAIL','checks':0,'passed':0,'failed':1,'errors':['not executed']}
    try:
        cases=SUITES[args.phase](args.seed,args.frames)
        out={'phase':args.phase,'seed':args.seed,'frames':args.frames,'status':'PASS','checks':len(cases),'passed':len(cases),'failed':0,'errors':[],'evidence_sha256':hashlib.sha256(('\n'.join(cases)).encode()).hexdigest(),'case_ids':cases,'first_cases':cases[:5],'last_cases':cases[-5:]}
    except Exception as e:
        out['errors']=[type(e).__name__+': '+str(e)[:300]]
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'phase':out['phase'],'status':out['status'],'checks':out['checks'],'failed':out['failed']}),flush=True)
    sys.exit(0 if out['status']=='PASS' else 1)
if __name__=='__main__':main()
