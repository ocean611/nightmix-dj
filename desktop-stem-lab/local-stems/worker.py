import os,sys,subprocess
from pathlib import Path
import numpy as np
import soundfile as sf
import torch
from demucs.pretrained import get_model
from demucs.apply import apply_model
p=Path(sys.argv[1]);src=p/'source' if (p/'source').exists() else p/'source.mp3'
import json
info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','json',str(src)]))
if float(info.get('format',{}).get('duration',0))>1800:raise RuntimeError('单曲请控制在30分钟以内')
subprocess.run(['ffmpeg','-v','error','-nostdin','-y','-i',str(src),'-ar','44100','-ac','2',str(p/'decoded.wav')],check=True)
torch.set_num_threads(min(6,os.cpu_count() or 2))
print('Loading htdemucs on local CPU',flush=True)
model=get_model('htdemucs');model.eval()
a,sr=sf.read(p/'decoded.wav',dtype='float32',always_2d=True)
if len(a)>44100*1800:raise RuntimeError('单曲请控制在30分钟以内')
wav=torch.from_numpy(a.T.copy());ref=wav.mean(0);mean=ref.mean();std=ref.std()
if std<1e-8:raise RuntimeError('音频是静音或没有有效信号')
with torch.inference_mode():
 stems=apply_model(model,((wav-mean)/std)[None],device='cpu',shifts=0,split=True,segment=6,overlap=.25,progress=True,num_workers=0)[0]
 stems=stems*std+mean
 # One shared gain keeps relative levels across all stems.
 gain=max(1.,float(stems.abs().max())/.99)
 for name,data in zip(model.sources,stems):sf.write(p/(name+'.wav'),(data/gain).T.numpy(),sr,subtype='PCM_24')
print('Finished: vocals / drums / bass / other',flush=True)
