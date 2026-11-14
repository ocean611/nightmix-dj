import asyncio,os,secrets,time,json,subprocess,uuid,shutil
from pathlib import Path
from fastapi import FastAPI,UploadFile,Header,HTTPException
from fastapi.responses import FileResponse
app=FastAPI(docs_url=None,redoc_url=None,openapi_url=None)
ROOT=Path('/data/jobs');ROOT.mkdir(parents=True,exist_ok=True)
KEY=Path('/data/access-key');KEY.write_text(secrets.token_urlsafe(24)) if not KEY.exists() else None
KEY.chmod(0o600)
lock=asyncio.Lock();jobs={}
def auth(key):
 if not key or not secrets.compare_digest(key,KEY.read_text().strip()):raise HTTPException(401,'分轨访问码不正确')
@app.get('/health')
def health():return {'status':'ok','model':'htdemucs','busy':lock.locked()}
async def process(jid):
 p=ROOT/jid;job=jobs[jid]
 try:
  job['status']='processing'
  env=os.environ.copy();env['OMP_NUM_THREADS']='1'
  with (p/'process.log').open('w') as log:
   proc=await asyncio.create_subprocess_exec('python','-m','demucs','-n','htdemucs','-d','cpu','-j','1','--shifts','0','--segment','2','--overlap','0.1','--out',str(p/'out'),str(p/'input.wav'),stdout=log,stderr=log,env=env)
   try:code=await asyncio.wait_for(proc.wait(),3600)
   except asyncio.TimeoutError:proc.kill();await proc.wait();raise RuntimeError('处理超时')
  if code:raise RuntimeError('模型处理失败，请检查服务器日志')
  for stem in ['vocals','drums','bass','other']:
   src=p/'out/htdemucs/input'/f'{stem}.wav'
   if not src.exists():raise RuntimeError('分轨输出不完整')
  job['status']='ready'
 except Exception as e:job['status']='failed';job['error']=str(e)
 finally:
  job['finished']=time.time();lock.release()
@app.post('/jobs')
async def upload(file:UploadFile,x_stem_key:str=Header(default='')):
 auth(x_stem_key)
 if lock.locked():raise HTTPException(429,'服务器正在处理另一首歌，请稍后再试')
 await lock.acquire();jid=uuid.uuid4().hex;p=ROOT/jid;p.mkdir()
 try:
  for old in ROOT.iterdir():
   if old.is_dir() and old!=p and time.time()-old.stat().st_mtime>86400:shutil.rmtree(old)
  size=0
  with (p/'source').open('wb') as f:
   while data:=await file.read(1048576):
    size+=len(data)
    if size>60*1048576:raise HTTPException(413,'文件不能超过 60 MB')
    f.write(data)
  probe=await asyncio.create_subprocess_exec('ffprobe','-v','error','-show_entries','format=format_name,duration:stream=codec_name,codec_type','-of','json',str(p/'source'),stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE)
  try:probeout,_=await asyncio.wait_for(probe.communicate(),20)
  except asyncio.TimeoutError:probe.kill();await probe.wait();raise HTTPException(400,'音频格式检测超时')
  if probe.returncode:raise HTTPException(400,'无法识别此音频，文件可能损坏或受 DRM 保护')
  metadata=json.loads(probeout);streams=[x for x in metadata.get('streams',[]) if x.get('codec_type')=='audio']
  if not streams:raise HTTPException(400,'文件没有可识别的音轨')
  detected_format=metadata.get('format',{}).get('format_name','unknown');codec=streams[0].get('codec_name','unknown')
  if float(metadata.get('format',{}).get('duration',0) or 0)>180.1:raise HTTPException(400,'已识别音频，但当前服务器分离单曲限 3 分钟')
  proc=await asyncio.create_subprocess_exec('ffmpeg','-v','error','-nostdin','-protocol_whitelist','file,pipe','-i',str(p/'source'),'-t','181','-ar','44100','-ac','2',str(p/'input.wav'),stdout=asyncio.subprocess.DEVNULL,stderr=asyncio.subprocess.DEVNULL)
  try:code=await asyncio.wait_for(proc.wait(),90)
  except asyncio.TimeoutError:proc.kill();await proc.wait();raise HTTPException(400,'解码超时')
  if code:raise HTTPException(400,'无法解码此音频')
  import wave
  with wave.open(str(p/'input.wav')) as w:duration=w.getnframes()/w.getframerate()
  if duration>180:raise HTTPException(400,'单曲不超过 3 分钟')
  token=secrets.token_urlsafe(24);jobs[jid]={'status':'queued','token':token,'duration':duration,'format':detected_format,'codec':codec};asyncio.create_task(process(jid));return {'id':jid,'token':token,'format':detected_format,'codec':codec,'duration':duration}
 except Exception:
  lock.release();shutil.rmtree(p,ignore_errors=True);raise
 finally:await file.close()
def jobauth(jid,token):
 job=jobs.get(jid)
 if not job or not secrets.compare_digest(token,job['token']):raise HTTPException(404)
 return job
@app.get('/jobs/{jid}')
def status(jid:str,x_job_token:str=Header(default='')):
 j=jobauth(jid,x_job_token);return {k:v for k,v in j.items() if k!='token'}
@app.get('/jobs/{jid}/{stem}')
def output(jid:str,stem:str,x_job_token:str=Header(default='')):
 j=jobauth(jid,x_job_token)
 if stem not in ['vocals','drums','bass','other'] or j['status']!='ready':raise HTTPException(404)
 return FileResponse(ROOT/jid/'out/htdemucs/input'/f'{stem}.wav',media_type='audio/wav',filename=f'{stem}.wav')
