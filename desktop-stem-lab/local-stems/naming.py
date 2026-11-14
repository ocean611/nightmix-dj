"""Names for exported audio; internal processing filenames stay stable."""
import json,re,zipfile,os,unicodedata
from pathlib import Path
KINDS={'source.mp3':'完整音频','vocals.wav':'人声','drums.wav':'鼓','bass.wav':'贝斯','other.wav':'其他乐器','four-stems.zip':'四轨分轨','process.log':'分轨日志','download.log':'下载日志'}
def clean(value,fallback):
 value=unicodedata.normalize('NFC',str(value or ''))
 value=re.sub(r'[\x00-\x1f\x7f/\\:*?"<>|]','_',value).strip(' .')
 return (value[:70] or fallback)
def infer(name,artist=''):
 title=re.sub(r'\.(mp3|m4a|wav|aac|flac|aiff|ogg|opus)$','',name or '',flags=re.I).strip()
 if ' - ' in title:
  left,right=title.split(' - ',1)
  if not artist or clean(left,'').casefold()==clean(artist,'').casefold():artist,title=left,right
 return {'title':title or '未命名歌曲','artist':artist or '未知作者'}
def filename(meta,key):return f"{clean(meta.get('title'),'未命名歌曲')} - {clean(meta.get('artist'),'未知作者')} - {KINDS[key]}{Path(key).suffix}"
def export_files(p,meta):
 out=p/'exports';out.mkdir(exist_ok=True)
 desired=set()
 for key in KINDS:
  if key=='four-stems.zip' or not (p/key).exists():continue
  target=out/filename(meta,key);desired.add(target.name)
  if not target.exists():os.link(p/key,target)
 if all((p/(name+'.wav')).exists() for name in ['vocals','drums','bass','other']) and meta.get('status')=='ready':
  target=out/filename(meta,'four-stems.zip');desired.add(target.name)
  if not target.exists() or any((p/(name+'.wav')).stat().st_mtime>target.stat().st_mtime for name in ['vocals','drums','bass','other']):
   tmp=out/'pack.tmp'
   with zipfile.ZipFile(tmp,'w',zipfile.ZIP_STORED) as z:
    for name in ['vocals','drums','bass','other']:
     key=name+'.wav';z.write(p/key,filename(meta,key))
   tmp.replace(target)
  (p/'four-stems.zip').unlink(missing_ok=True)
 for old in out.iterdir():
  if old.is_file() and old.name not in desired:old.unlink()
 return {key:filename(meta,key) for key in KINDS if (out/filename(meta,key)).exists()}
