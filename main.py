#!/usr/bin/env python3
"""Deterministic, offline fantasy-galaxy artwork generator."""
from __future__ import annotations
import math, os, random, struct, zlib

W = H = 1024
SEED = 731904

def clamp(v):
    return max(0, min(255, int(v + 0.5)))

def h2(x, y):
    n = (x * 374761393 + y * 668265263 + SEED * 1442695041) & 0xffffffff
    n = ((n ^ (n >> 13)) * 1274126177) & 0xffffffff
    return (n ^ (n >> 16)) / 4294967295.0

def chunk(kind, data):
    body = kind + data
    return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xffffffff)

def save_png(path, pixels):
    raw = bytearray()
    for y in range(H):
        raw.append(0)
        raw.extend(pixels[y * W * 3:(y + 1) * W * 3])
    data = (b"\x89PNG\r\n\x1a\n" +
        chunk(b"IHDR", struct.pack(">2I5B", W, H, 8, 2, 0, 0, 0)) +
        chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(data)

def glow(buf, cx, cy, radius, color, strength=1.0):
    extent = radius * 3
    for y in range(max(0, int(cy-extent)), min(H, int(cy+extent+1))):
        for x in range(max(0, int(cx-extent)), min(W, int(cx+extent+1))):
            d2 = (x-cx)**2 + (y-cy)**2
            g = strength * math.exp(-d2 / max(1, radius*radius*.55))
            if d2 > radius*radius*9 or g < .004: continue
            i = (y*W+x)*3
            for k in range(3): buf[i+k] = clamp(buf[i+k] + color[k]*g)

def render():
    p = bytearray(W*H*3)
    cx, cy = .495, .485
    grid = [[h2(x,y) for x in range(65)] for y in range(65)]
    for y in range(H):
        ny = (y/(H-1)-cy)*1.85
        gy, iy = y/16, int(y/16)
        fy = gy-iy
        for x in range(W):
            nx = (x/(W-1)-cx)*1.85
            gx, ix = x/16, int(x/16)
            fx = gx-ix
            n0 = grid[iy][ix] + (grid[iy][ix+1]-grid[iy][ix])*fx
            n1 = grid[iy+1][ix] + (grid[iy+1][ix+1]-grid[iy+1][ix])*fx
            noise = n0 + (n1-n0)*fy
            r = math.hypot(nx*.92, ny*1.05)
            a = math.atan2(ny,nx)
            rr = math.hypot(nx*.97,ny*1.08)
            cloud1 = math.exp(-(((nx+.42)/.34)**2+((ny-.30)/.27)**2)*2)
            cloud2 = math.exp(-(((nx-.48)/.32)**2+((ny+.22)/.42)**2)*2)
            cloud3 = math.exp(-(((nx+.02)/.52)**2+((ny+.53)/.20)**2)*2)
            arm = math.exp(-((math.sin(a-3.15*math.log(max(.075,rr)))/.145)**2))
            disk = math.exp(-((rr-.40)/.30)**2)
            arm_light = arm*disk*math.exp(-rr*.62)
            core = math.exp(-(rr/.115)**2)
            ring = math.exp(-((rr-.19)/.035)**2)
            dust = math.exp(-((ny+.075*math.sin(a*2))/.026)**2)*disk
            base = 2 + 5.5*max(0,1-(r/1.36)**2)
            grain = (noise-.5)*2
            red = base+17*cloud1+8*cloud2+137*arm_light+235*core+19*ring+20*cloud3+3*grain
            green = base*1.2+13*cloud1+25*cloud2+94*arm_light+192*core+13*ring+29*cloud3+2.4*grain
            blue = base*2.5+42*cloud1+66*cloud2+43*arm_light+105*core+5*ring+55*cloud3+2*grain
            red *= 1-.47*dust; green *= 1-.56*dust; blue *= 1-.42*dust
            cyan = 17*cloud2*math.exp(-((rr-.54)/.23)**2)
            red += .18*cyan; green += .68*cyan; blue += 1.05*cyan
            i=(y*W+x)*3
            p[i:i+3]=bytes((clamp(red),clamp(green),clamp(blue)))
    # Shadowed planet and illuminated limb.
    px,py,pr=805.,782.,116.
    for y in range(int(py-pr-3),int(py+pr+4)):
        for x in range(int(px-pr-3),int(px+pr+4)):
            dx,dy=x-px,y-py; d=math.hypot(dx,dy)
            if d>pr+3: continue
            i=(y*W+x)*3
            if d<=pr:
                light=max(0.,-((dx*.55+dy*.82)/pr)+.35)
                limb=math.sqrt(max(0.,1-(d/pr)**2)); shade=.12+.32*light+.10*limb
                p[i:i+3]=bytes((clamp(5+42*shade),clamp(7+56*shade),clamp(17+91*shade)))
            else:
                rim=1-(d-pr)/3
                p[i]=clamp(p[i]+95*rim); p[i+1]=clamp(p[i+1]+66*rim); p[i+2]=clamp(p[i+2]+24*rim)
    rng=random.Random(SEED)
    for _ in range(1750):
        sx,sy=rng.randrange(W),rng.randrange(H)
        size=rng.choices([0,1,2],[.82,.16,.02])[0]
        t=rng.random()
        col=(142,190,255) if t<.2 else ((255,222,160) if t<.42 else (220,229,255))
        if size: glow(p,sx,sy,9 if size==2 else 4,col,.36 if size==2 else .22)
        i=(sy*W+sx)*3
        for k in range(3): p[i+k]=clamp(p[i+k]+col[k])
        if size==2:
            for off in range(-7,8):
                v=max(0,1-abs(off)/8)*.42
                if 0<=sx+off<W:
                    j=(sy*W+sx+off)*3
                    for k in range(3): p[j+k]=clamp(p[j+k]+col[k]*v)
                if 0<=sy+off<H:
                    j=((sy+off)*W+sx)*3
                    for k in range(3): p[j+k]=clamp(p[j+k]+col[k]*v)
    for sx,sy,rad in ((510,492,26),(294,310,17),(690,220,13)):
        glow(p,sx,sy,rad*3,(255,203,112),.45)
        for off in range(-rad*2,rad*2+1):
            fade=max(0,1-abs(off)/(rad*2+1))
            for xx,yy in ((sx+off,sy),(sx,sy+off)):
                if 0<=xx<W and 0<=yy<H:
                    j=(yy*W+xx)*3
                    for k,c in enumerate((255,220,160)): p[j+k]=clamp(p[j+k]+c*fade*.35)
        glow(p,sx,sy,3,(255,246,218),1.5)
    # Broken, dust-laden logarithmic arms.
    for arm_index in range(2):
        for step in range(1450):
            t=.10+step/1449*(math.pi*5.6)
            radius=.045*math.exp(.205*t)
            if radius>.63 or h2(step,arm_index+170)<.24: continue
            angle=t+arm_index*math.pi+.18
            sx=W*cx+math.cos(angle)*radius*W*.70
            sy=H*cy+math.sin(angle)*radius*H*.47
            strength=.30+.45*h2(step+23,arm_index+8)
            glow(p,sx,sy,2,(255,198,105),strength)
            if step%13==0: glow(p,sx,sy,5,(255,222,158),.24)
    return p

def main():
    os.makedirs("/output",exist_ok=True)
    save_png("/output/entry.png",render())

if __name__=="__main__": main()
