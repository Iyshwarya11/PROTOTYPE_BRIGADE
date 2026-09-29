import argparse
import csv
import math
from pathlib import Path
import cv2
import numpy as np


def ca_cfar(power, train_r=6, train_d=5, guard_r=1, guard_d=1, pfa=1e-3):
    rows, cols = power.shape
    detections = []
    total_train = ((2*(train_r+guard_r)+1)*(2*(train_d+guard_d)+1)
                   - (2*guard_r+1)*(2*guard_d+1))
    alpha = total_train * (pfa ** (-1.0/total_train) - 1.0)
    threshold_map = np.zeros_like(power, dtype=np.float32)

    for r in range(train_r+guard_r, rows-train_r-guard_r):
        for d in range(train_d+guard_d, cols-train_d-guard_d):
            window = power[r-(train_r+guard_r):r+train_r+guard_r+1,
                           d-(train_d+guard_d):d+train_d+guard_d+1]
            mask = np.ones(window.shape, dtype=bool)
            gr0 = train_r
            gd0 = train_d
            mask[gr0-guard_r:gr0+guard_r+1,
                 gd0-guard_d:gd0+guard_d+1] = False
            noise = float(np.mean(window[mask]))
            threshold = alpha * max(noise, 1e-9)
            threshold_map[r, d] = threshold
            if power[r, d] > threshold:
                snr = 10*np.log10(max(power[r,d],1e-9)/max(noise,1e-9))
                detections.append((r, d, float(power[r,d]), float(snr)))
    return detections, threshold_map


def cluster_radar(detections, range_merge=3, doppler_merge=3):
    """Simple connected grouping of nearby CFAR cells."""
    groups = []
    for det in detections:
        r,d,p,snr = det
        placed = False
        for g in groups:
            gr = np.mean([x[0] for x in g])
            gd = np.mean([x[1] for x in g])
            if abs(r-gr) <= range_merge and abs(d-gd) <= doppler_merge:
                g.append(det); placed = True; break
        if not placed:
            groups.append([det])
    out=[]
    for g in groups:
        strongest=max(g,key=lambda x:x[2])
        out.append({
            'range_bin': float(np.mean([x[0] for x in g])),
            'doppler_bin': float(np.mean([x[1] for x in g])),
            'power': strongest[2],
            'snr_db': strongest[3],
            'cells': len(g)
        })
    return out


def thermal_hotspots(gray8, min_area=80, max_area_ratio=0.45):
    """Adaptive thermal hotspot POC using local statistics on an 8-bit thermal image."""
    blur = cv2.GaussianBlur(gray8, (7,7), 0)
    mean, std = cv2.meanStdDev(blur)
    threshold = float(mean[0,0] + 2.0*std[0,0])
    threshold = max(120.0, min(threshold, 245.0))
    _, mask = cv2.threshold(blur, threshold, 255, cv2.THRESH_BINARY)

    kernel = np.ones((5,5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    contours,_ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    h,w=gray8.shape
    detections=[]
    for c in contours:
        area=cv2.contourArea(c)
        if area < min_area or area > h*w*max_area_ratio:
            continue
        x,y,bw,bh=cv2.boundingRect(c)
        roi=gray8[y:y+bh,x:x+bw]
        peak=float(np.max(roi)) if roi.size else 0
        avg=float(np.mean(roi)) if roi.size else 0
        fill=area/(bw*bh+1e-9)
        detections.append({'cx':x+bw/2,'cy':y+bh/2,'area':area,
                           'peak':peak,'average':avg,'fill':fill,
                           'bbox':(x,y,bw,bh)})
    detections.sort(key=lambda z:z['peak'], reverse=True)
    return detections, mask, threshold


def associate(radar_objects, thermal_objects, gate=80):
    pairs=[]
    for ro in radar_objects:
        # POC mapping: range bin -> horizontal thermal coordinate.
        # Replace with calibrated radar-to-camera projection in the real system.
        rx = ro['range_bin'] / 96.0 * 1280.0
        ry = ro['doppler_bin'] / 64.0 * 720.0
        best=None
        for i,to in enumerate(thermal_objects):
            dist=math.hypot(rx-to['cx'], ry-to['cy'])
            if dist <= gate and (best is None or dist < best[0]):
                best=(dist,i,to)
        if best:
            dist,i,to=best
            radar_conf=np.clip((ro['snr_db']-3)/20,0,1)
            thermal_conf=np.clip((to['peak']-120)/120,0,1)
            proximity=np.clip(1-dist/gate,0,1)
            fused=.45*radar_conf+.40*thermal_conf+.15*proximity
            pairs.append((ro,to,float(fused),float(dist)))
    return pairs


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--radar', default='radar_power.csv')
    ap.add_argument('--thermal', default='thermal_8bit.png')
    ap.add_argument('--output', default='thermal_radar_result.png')
    args=ap.parse_args()

    radar=np.loadtxt(args.radar, delimiter=',')
    if radar.ndim != 2: raise ValueError('Radar CSV must contain a 2D power matrix')
    thermal=cv2.imread(args.thermal, cv2.IMREAD_GRAYSCALE)
    if thermal is None: raise FileNotFoundError(args.thermal)

    rd,thmap=ca_cfar(radar)
    ro=cluster_radar(rd)
    to,mask,thr=thermal_hotspots(thermal)
    pairs=associate(ro,to)

    print('\n========== ADVANCED THERMAL + RADAR ==========')
    print(f'Radar matrix          : {radar.shape[0]} x {radar.shape[1]}')
    print(f'CFAR detections       : {len(rd)} cells')
    print(f'Radar objects         : {len(ro)} clusters')
    print(f'Thermal hotspots      : {len(to)}')
    print(f'Thermal threshold     : {thr:.1f}/255')
    print(f'Associated objects    : {len(pairs)}')
    print('-----------------------------------------------')
    for n,(r,t,conf,dist) in enumerate(pairs,1):
        print(f'Object {n}: radar range-bin={r["range_bin"]:.1f}, '
              f'doppler-bin={r["doppler_bin"]:.1f}, SNR={r["snr_db"]:.1f} dB | '
              f'thermal peak={t["peak"]:.0f}/255 | fused confidence={conf*100:.1f}%')
    if not pairs:
        print('No radar-thermal association passed the gate.')
    print('Fail-safe: if thermal becomes unreliable, use radar as the primary detection sensor.')
    print('==============================================\n')

    # Create a simple diagnostic image.
    vis=cv2.cvtColor(thermal,cv2.COLOR_GRAY2BGR)
    vis=cv2.resize(vis,(1280,720))
    for i,t in enumerate(to,1):
        x,y,bw,bh=t['bbox']; sx=1280/thermal.shape[1]; sy=720/thermal.shape[0]
        x,y,bw,bh=int(x*sx),int(y*sy),int(bw*sx),int(bh*sy)
        cv2.rectangle(vis,(x,y),(x+bw,y+bh),(0,255,255),2)
        cv2.putText(vis,f'T{i} peak={t["peak"]:.0f}',(x,y-8),cv2.FONT_HERSHEY_SIMPLEX,.5,(255,255,255),1)
    for i,(r,t,conf,dist) in enumerate(pairs,1):
        cv2.circle(vis,(int(t['cx']*sx),int(t['cy']*sy)),8,(0,0,255),-1)
        cv2.putText(vis,f'FUSED {conf*100:.0f}%',(int(t['cx']*sx)+10,int(t['cy']*sy)),cv2.FONT_HERSHEY_SIMPLEX,.55,(255,255,255),2)
    cv2.imwrite(args.output,vis)
    print('Saved diagnostic image:',args.output)

if __name__=='__main__': main()
