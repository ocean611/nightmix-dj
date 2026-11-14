import asyncio,json,os,secrets,sys,uuid,zipfile,re
from pathlib import Path
from urllib.parse import urlparse
from fastapi import FastAPI,UploadFile,HTTPException,Request
from fastapi.responses import FileResponse,HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel
from naming import infer,filename,export_files
ROOT=Path(__file__).resolve().parent;DATA=ROOT/'data';DATA.mkdir(exist_ok=True)
TOKEN=secrets.token_urlsafe(32);lock=asyncio.Lock()
app=FastAPI(docs_url=None,redoc_url=None,openapi_url=None)
app.add_middleware(TrustedHostMiddleware,allowed_hosts=['127.0.0.1','localhost'])
@app.middleware('http')
async def protect(request:Request,call_next):
 if request.method not in ('GET','HEAD') and not secrets.compare_digest(request.headers.get('x-local-token',''),TOKEN):
  from fastapi.responses import JSONResponse
  return JSONResponse({'detail':'请刷新本机页面后重试'},status_code=403)
 return await call_next(request)
app.mount('/static',StaticFiles(directory=ROOT/'static'),name='static')
@app.get('/')
def home():return HTMLResponse((ROOT/'static/index.html').read_text().replace('__TOKEN__',TOKEN))
def folder(jid):
 if not re.fullmatch('[a-f0-9]{32}',jid):raise HTTPException(404)
 p=DATA/jid
 if not p.exists():raise HTTPException(404)
 return p
def state(p,**fields):
 old=json.loads((p/'status.json').read_text()) if (p/'status.json').exists() else {}
 old.update(fields);tmp=p/'status.tmp';tmp.write_text(json.dumps(old,ensure_ascii=False));tmp.replace(p/'status.json')
def new(name):
 p=DATA/uuid.uuid4().hex;p.mkdir();state(p,name=name,**infer(name),status='importing',message='准备音频');return p
async def command(args,log,timeout=3600):
 with log.open('a') as f:
  proc=await asyncio.create_subprocess_exec(*args,stdout=f,stderr=f,env={**os.environ,'TORCH_HOME':str(DATA/'models'),'SSL_CERT_FILE':'/etc/ssl/cert.pem'})
  try:code=await asyncio.wait_for(proc.wait(),timeout)
  except asyncio.TimeoutError:proc.kill();await proc.wait();raise RuntimeError('处理超时，请查看日志')
 if code:raise RuntimeError(log.read_text(errors='replace')[-1400:])
async def separate(p):
 async with lock:
  try:
   state(p,status='processing',message='电脑正在分轨，首次会下载模型')
   await command([sys.executable,str(ROOT/'worker.py'),str(p)],p/'process.log',14400)
   state(p,status='ready',message='四轨已完成，可以下载或试听')
   export_files(p,json.loads((p/'status.json').read_text()))
  except Exception as e:state(p,status='failed',message=str(e)[-1600:])
@app.get('/api/jobs')
def jobs():
 result=[]
 for p in sorted(DATA.iterdir(),key=lambda x:x.stat().st_mtime,reverse=True):
  if not (p/'status.json').exists():continue
  item=json.loads((p/'status.json').read_text());item['id']=p.name
  item['filenames']={key:filename(item,key) for key in ['source.mp3','vocals.wav','drums.wav','bass.wav','other.wav','four-stems.zip']}
  if item['status']=='processing' and (p/'process.log').exists():
   percentages=re.findall(r'(\d+)%\|',(p/'process.log').read_text(errors='replace'))
   if percentages:item['progress']=int(percentages[-1])
  result.append(item)
 return result
@app.post('/api/upload')
async def upload(file:UploadFile):
 p=new(file.filename or '本地音频');size=0
 try:
  with (p/'source').open('wb') as out:
   while chunk:=await file.read(1024*1024):
    size+=len(chunk)
    if size>500*1024*1024:raise HTTPException(413,'文件请控制在500MB以内')
    out.write(chunk)
  await command(['ffmpeg','-v','error','-nostdin','-y','-i',str(p/'source'),'-vn','-c:a','libmp3lame','-q:a','0',str(p/'source.mp3')],p/'download.log',300)
  probe=await asyncio.create_subprocess_exec('ffprobe','-v','error','-show_entries','format_tags=title,artist','-of','json',str(p/'source'),stdout=asyncio.subprocess.PIPE)
  raw,_=await probe.communicate();tags=json.loads(raw).get('format',{}).get('tags',{});tags={k.lower():v for k,v in tags.items()}
  if tags.get('title') or tags.get('artist'):
   meta=infer(file.filename or '本地音频');state(p,title=tags.get('title') or meta['title'],artist=tags.get('artist') or meta['artist'])
  state(p,status='downloaded',message='已导入，点击开始分轨');export_files(p,json.loads((p/'status.json').read_text()));return {'id':p.name}
 except Exception:
  import shutil
  shutil.rmtree(p);raise
 finally:await file.close()
class Search(BaseModel):query:str
@app.post('/api/search')
async def search(body:Search):
 q=body.query.strip()
 if not q or len(q)>200:raise HTTPException(400,'请输入歌名和歌手')
 args=[sys.executable,'-m','yt_dlp','--ignore-config','--flat-playlist','--dump-single-json','--no-warnings','ytsearch5:'+q]
 proc=await asyncio.create_subprocess_exec(*args,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE)
 try:out,err=await asyncio.wait_for(proc.communicate(),60)
 except asyncio.TimeoutError:proc.kill();await proc.wait();raise HTTPException(504,'搜索超时，请检查电脑网络或改用音频导入')
 if proc.returncode:raise HTTPException(502,err.decode(errors='replace')[-700:])
 return [{'title':x.get('title'),'artist':x.get('channel') or x.get('uploader'),'duration':x.get('duration'),'url':x.get('webpage_url') or x.get('url')} for x in json.loads(out).get('entries',[]) if x]
class Download(BaseModel):url:str;title:str='在线音频';artist:str=''
async def fetch_audio(p,url):
 async with lock:
  try:
   state(p,status='downloading',message='下载并转换MP3')
   await command([sys.executable,'-m','yt_dlp','--ignore-config','--write-info-json','--no-playlist','--max-filesize','500M','--socket-timeout','30','--retries','2','-f','bestaudio/best','-x','--audio-format','mp3','--audio-quality','0','-o',str(p/'source.%(ext)s'),'--',url],p/'download.log')
   if not (p/'source.mp3').exists():raise RuntimeError('未获得MP3，请导入本地音频')
   infofile=p/'source.info.json'
   if infofile.exists():
    info=json.loads(infofile.read_text());meta=infer(info.get('title') or '在线音频',info.get('artist') or '')
    if info.get('track'):meta['title']=info['track']
    state(p,**meta)
   state(p,status='downloaded',message='MP3已就绪，可以开始分轨');export_files(p,json.loads((p/'status.json').read_text()))
  except Exception as e:state(p,status='failed',message=str(e)[-1600:])
@app.post('/api/download')
async def download(body:Download):
 u=urlparse(body.url)
 if u.scheme!='https' or not u.hostname or u.hostname in ('localhost','127.0.0.1','::1'):raise HTTPException(400,'请输入公开HTTPS音频或视频页面链接')
 p=new(body.title[:200]);state(p,**infer(body.title,body.artist));state(p,status='queued',message='等待下载');asyncio.create_task(fetch_audio(p,body.url));return {'id':p.name}
@app.post('/api/jobs/{jid}/split')
async def split(jid:str):
 p=folder(jid);s=json.loads((p/'status.json').read_text())
 if s['status'] not in ('downloaded','failed','ready'):raise HTTPException(409,'任务正在处理中')
 if not (p/'source').exists() and not (p/'source.mp3').exists():raise HTTPException(400,'没有音频，请重新导入或下载')
 state(p,status='queued',message='等待分轨');asyncio.create_task(separate(p));return {'ok':True}
class Metadata(BaseModel):title:str;artist:str
@app.post('/api/jobs/{jid}/metadata')
async def metadata(jid:str,body:Metadata):
 p=folder(jid);meta=json.loads((p/'status.json').read_text())
 if meta['status'] not in ('ready','downloaded','failed'):raise HTTPException(409,'请等待当前任务完成后修改')
 if not body.title.strip() or not body.artist.strip():raise HTTPException(400,'请填写歌名和作者')
 state(p,title=body.title.strip()[:100],artist=body.artist.strip()[:100]);export_files(p,json.loads((p/'status.json').read_text()));return {'ok':True}
@app.get('/api/jobs/{jid}/files/{name}')
def file(jid:str,name:str):
 if name not in ['vocals.wav','drums.wav','bass.wav','other.wav','four-stems.zip','source.mp3','process.log','download.log']:raise HTTPException(404)
 p=folder(jid);meta=json.loads((p/'status.json').read_text());target=p/'exports'/filename(meta,name)
 if not target.exists():export_files(p,meta)
 if not target.exists():raise HTTPException(404)
 return FileResponse(target,filename=target.name)
@app.on_event('startup')
def recover():
 for p in DATA.iterdir():
  if (p/'status.json').exists() and json.loads((p/'status.json').read_text())['status'] in ('queued','processing','downloading','importing'):state(p,status='failed',message='上次服务已停止，可重新分轨或导入')
 for p in DATA.iterdir():
  if (p/'status.json').exists():
   meta=json.loads((p/'status.json').read_text())
   if 'title' not in meta:state(p,**infer(meta.get('name','')))
   export_files(p,json.loads((p/'status.json').read_text()))
if __name__=='__main__':
 import uvicorn
 uvicorn.run(app,host='127.0.0.1',port=8765)
