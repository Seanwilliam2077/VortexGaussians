"""Make a fixed sRGB display preview from the archived native scene-linear RGB."""
import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image


def convert(src,dest):
    with np.load(src,allow_pickle=False) as archive:
        rgba=archive["pixels"]
    if rgba.shape!=(180,320,4) or not np.isfinite(rgba).all():
        raise ValueError("Expected the finite native scene-linear RGBA image")
    rgb=rgba[:,:,:3].astype(np.float64)
    clipped=np.clip(rgb,0,1)
    srgb=np.where(clipped<=0.0031308,12.92*clipped,1.055*clipped**(1/2.4)-0.055)
    pixels=np.rint(255*srgb).astype(np.uint8)
    Image.fromarray(pixels).save(dest)
    with Image.open(dest) as png:
        if not np.array_equal(np.asarray(png),pixels):
            raise ValueError("Display preview did not round-trip")
    return dict(size=[320,180],exposure=1,transfer="clip [0,1], standard sRGB, nearest 8-bit RGB",
                alpha="opaque display of the native RGB channels",clipped_low_rgb=int(np.count_nonzero(rgb<0)),
                clipped_high_rgb=int(np.count_nonzero(rgb>1)),alpha_range=[float(rgba[...,3].min()),float(rgba[...,3].max())])


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("src",type=Path)
    p.add_argument("dest",type=Path)
    args=p.parse_args()
    print(json.dumps(convert(args.src,args.dest),indent=2))
