"""Bound peak memory with isolated eight-second Demucs subprocesses.
Crossfade overlapping chunks and stream final WAVs to disk.
"""
import sys,subprocess,wave,shutil,os
from pathlib import Path
import numpy as np
p=Path(sys.argv[1]);names=['vocals','drums','bass','other'];rate=44100
chunk=8*rate;overlap=rate//2;step=chunk-overlap
out=p/'out/htdemucs/input';out.mkdir(parents=True,exist_ok=True)
handles={};tails={}
try:
 for name in names:
  w=wave.open(str(out/(name+'.wav')),'wb');w.setparams((2,2,rate,0,'NONE','not compressed'));handles[name]=w
 with wave.open(str(p/'input.wav')) as source:
  total=source.getnframes();start=0;index=0
  while start<total:
   source.setpos(start);frames=min(chunk,total-start);raw=source.readframes(frames)
   temp=p/'chunk';temp.mkdir(exist_ok=True)
   with wave.open(str(temp/'piece.wav'),'wb') as w:
    w.setparams((2,2,rate,0,'NONE','not compressed'));w.writeframes(raw)
   print(f'Chunk {index+1}: {start/rate:.1f}/{total/rate:.1f}s',flush=True)
   subprocess.run([sys.executable,'-m','demucs','-n','htdemucs','-d','cpu','-j','1','--shifts','0','--segment','2','--overlap','0.1','--out',str(temp/'out'),str(temp/'piece.wav')],check=True)
   last=start+frames>=total
   for name in names:
    with wave.open(str(temp/'out/htdemucs/piece'/(name+'.wav'))) as w:
     a=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').reshape(-1,2).astype(np.float32)
    if index:
     n=min(len(tails[name]),len(a));fade=np.linspace(0,1,n,dtype=np.float32)[:,None];a[:n]=tails[name][:n]*(1-fade)+a[:n]*fade
    if not last:tails[name]=a[-overlap:].copy();a=a[:-overlap]
    handles[name].writeframes(np.clip(a,-32768,32767).astype('<i2').tobytes())
   shutil.rmtree(temp)
   if last:break
   start+=step;index+=1
finally:
 for w in handles.values():w.close()
