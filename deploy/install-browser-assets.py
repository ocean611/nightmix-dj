"""Install pinned browser runtime and checksum-verified model on the server."""
from pathlib import Path
import urllib.request,tarfile,io,hashlib,shutil
root=Path(__file__).resolve().parents[1];dest=root/'public/local-ai';dest.mkdir(exist_ok=True)
with urllib.request.urlopen('https://registry.npmjs.org/onnxruntime-web/-/onnxruntime-web-1.22.0.tgz',timeout=90) as r:data=r.read()
with tarfile.open(fileobj=io.BytesIO(data),mode='r:gz') as archive:
 for member in archive.getmembers():
  if member.isfile() and member.name.startswith('package/dist/') and '/' not in member.name[len('package/dist/'):]:
   name=Path(member.name).name
   if name.endswith(('.mjs','.wasm')):(dest/name).write_bytes(archive.extractfile(member).read())
  elif member.isfile() and member.name in ['package/LICENSE','package/ThirdPartyNotices.txt']:(dest/Path(member.name).name).write_bytes(archive.extractfile(member).read())
expected='d05c269d0178d2a72ad484b10b11dd370193fc923201c3b27a99f848745db70a'
model=dest/'htdemucs.onnx'
if model.exists() and hashlib.sha256(model.read_bytes()).hexdigest()==expected:print('Model already verified');raise SystemExit
for host in ['https://huggingface.co','https://hf-mirror.com']:
 try:
  temp=dest/'install.part'
  with urllib.request.urlopen(host+'/StemSplitio/htdemucs-onnx/resolve/main/htdemucs_fp16weights.onnx',timeout=180) as src,temp.open('wb') as out:shutil.copyfileobj(src,out)
  if hashlib.sha256(temp.read_bytes()).hexdigest()!=expected:raise ValueError('Model checksum mismatch')
  temp.rename(model);print('Model verified');break
 except Exception as error:print(type(error).__name__)
else:raise SystemExit('Model download failed')
