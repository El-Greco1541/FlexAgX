"""Offline demonstration (no network): python -m flexagx.cli in.png out.png"""
import argparse,base64
from pathlib import Path
from .contracts import Settings
from .compute import png_decode,png_encode,observe,make_lut,render_pixels
from .controller import SessionStore


def main():
    parser=argparse.ArgumentParser(description='Research CPU reference port of FlexAgX')
    parser.add_argument('input_png',type=Path)
    parser.add_argument('output_png',type=Path)
    parser.add_argument('--frame-index',type=int,default=0)
    parser.add_argument('--dt-ms',type=float,default=16.667)
    parser.add_argument('--detail',type=float,default=20)
    parser.add_argument('--strength',type=float,default=100)
    args=parser.parse_args()
    settings=Settings(LocalDetail=args.detail,OverallStrength=args.strength)
    b64=base64.b64encode(args.input_png.read_bytes()).decode('ascii')
    image=png_decode(b64)
    if settings.OverallStrength<=0:
        result=image
    else:
        obs=observe(image[...,:3],args.frame_index,settings)
        control=SessionStore().step('cli',obs,settings,args.dt_ms)
        lut=make_lut(control.gain,control.knee,settings.ShadowPreservation,
                     settings.InputEncoding,settings.OutputEncoding)
        result=render_pixels(image,settings,lut.lut,control.gain_ev)
    args.output_png.write_bytes(base64.b64decode(png_encode(result)))
    print('Written',args.output_png,'— CPU approximation, not GPU-certified')


if __name__=='__main__': main()
