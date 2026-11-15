/* Bounded-memory multiband onset/period estimator. BPM is evidence, not a guarantee of metrical level. */
const mod=(x,n)=>(x%n+n)%n, clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
function quantile(a,q){if(!a.length)return 0;const b=Array.from(a).sort((x,y)=>x-y);return b[Math.floor((b.length-1)*q)]}
function fft(real,imag){const n=real.length;for(let i=1,j=0;i<n;i++){let bit=n>>1;for(;j&bit;bit>>=1)j^=bit;j^=bit;if(i<j){[real[i],real[j]]=[real[j],real[i]]}}for(let len=2;len<=n;len<<=1){const angle=-2*Math.PI/len,wr=Math.cos(angle),wi=Math.sin(angle);for(let i=0;i<n;i+=len){let ar=1,ai=0;for(let j=0;j<len/2;j++){const u=i+j,v=u+len/2,tr=ar*real[v]-ai*imag[v],ti=ar*imag[v]+ai*real[v];real[v]=real[u]-tr;imag[v]=imag[u]-ti;real[u]+=tr;imag[u]+=ti;const next=ar*wr-ai*wi;ai=ar*wi+ai*wr;ar=next}}}}
function features(samples,sr){
 const size=512,hop=Math.round(sr/200),fps=sr/hop,n=Math.floor(samples.length/hop),onset=Array.from({length:3},()=>new Float32Array(n)),real=new Float64Array(size),imag=new Float64Array(size),last=new Float64Array(size/2),window=Float64Array.from({length:size},(_,i)=>.5-.5*Math.cos(2*Math.PI*i/(size-1)));
 let rms=0;for(let i=0;i<samples.length;i+=31)rms+=samples[i]**2;rms=Math.sqrt(rms/Math.ceil(samples.length/31));if(rms<1e-6)return {onset,events:[[],[],[]],fps,n};const gain=.15/rms;
 for(let i=0;i<n;i++){const first=i*hop-size/2;for(let j=0;j<size;j++)real[j]=(samples[first+j]||0)*window[j];imag.fill(0);fft(real,imag);for(let k=1;k<size/2;k++){const mag=Math.log1p(100*gain*Math.hypot(real[k],imag[k])/size),rise=Math.max(0,mag-last[k]),band=k*sr/size<180?0:k*sr/size<1800?1:2;onset[band][i]+=rise;last[k]=mag}}
 for(const a of onset){let baseline=0;for(let i=0;i<n;i++){const v=a[i];baseline+=.03*(v-baseline);a[i]=Math.max(0,v-baseline*.8)}}
 const events=onset.map(a=>{const peak=quantile(a,.99),threshold=Math.max(.0003,peak*.07),events=[];let lastTime=-100;if(peak<.0005)return events;for(let i=2;i<n-2;i++){if(a[i]<threshold||a[i]<a[i-1]||a[i]<=a[i+1])continue;const den=a[i-1]-2*a[i]+a[i+1],delta=den?clamp(.5*(a[i-1]-a[i+1])/den,-.5,.5):0;const t=(i+delta)/fps+size/(4*sr);if(t-lastTime<.065){if(a[i]>events.at(-1)?.w)events.pop();else continue}events.push({t,w:a[i]});lastTime=t}return events});return {onset,events,fps,n};
}
function correlationCandidates(f,start,end){
 const {onset,fps}=f,first=Math.floor(fps*.25),last=Math.ceil(fps*1.5),a=Math.floor(start*fps),b=Math.min(f.n,Math.floor(end*fps)),scores=new Float64Array(last+2);
 for(const band of onset){let norm=0;for(let i=a;i<b;i++)norm+=band[i]*band[i];if(norm<1e-8)continue;for(let lag=first-1;lag<=last+1;lag++){let sum=0;for(let i=a+lag;i<b;i++)sum+=band[i]*band[i-lag];scores[lag]+=sum/norm}}
 const peaks=[];for(let lag=first;lag<=last;lag++){if(scores[lag]<=scores[lag-1]||scores[lag]<scores[lag+1])continue;const den=scores[lag-1]-2*scores[lag]+scores[lag+1],delta=den?clamp(.5*(scores[lag-1]-scores[lag+1])/den,-.5,.5):0;peaks.push({bpm:60*fps/(lag+delta),strength:scores[lag]})}return peaks.sort((a,b)=>b.strength-a.strength).slice(0,10);
}
function fitGrid(events,bpm,start,end){
 const selected=events.filter(e=>e.t>=start&&e.t<=end);if(selected.length<6)return null;let period=60/bpm;const bins=new Float64Array(120);
 for(const e of selected){const k=Math.round(mod(e.t,period)/period*bins.length)%bins.length;for(let d=-2;d<=2;d++)bins[mod(k+d,bins.length)]+=e.w*(3-Math.abs(d))}
 let k=0;for(let i=1;i<bins.length;i++)if(bins[i]>bins[k])k=i;let offset=k/bins.length*period,accepted=[];
 for(let iter=0;iter<4;iter++){const tolerance=Math.min(.045,period*.12);accepted=[];let sw=0,sx=0,sy=0,sxx=0,sxy=0;
 for(const e of selected){const beat=Math.round((e.t-offset)/period),err=e.t-(offset+beat*period);if(Math.abs(err)>tolerance)continue;const weight=e.w*(1-.5*Math.abs(err)/tolerance);accepted.push({...e,beat});sw+=weight;sx+=weight*beat;sy+=weight*e.t;sxx+=weight*beat*beat;sxy+=weight*beat*e.t}
 const den=sw*sxx-sx*sx;if(accepted.length<6||Math.abs(den)<1e-7)return null;const newPeriod=(sw*sxy-sx*sy)/den;if(Math.abs(newPeriod/(60/bpm)-1)>.025)return null;period=newPeriod;offset=(sy-period*sx)/sw;
 }
 let err=0,weight=0;const unique=new Set();for(const e of accepted){err+=e.w*(e.t-offset-e.beat*period)**2;weight+=e.w;unique.add(e.beat)}
 const span=accepted.at(-1).t-accepted[0].t,possible=Math.max(1,Math.round(span/period)+1),coverage=Math.min(1,unique.size/possible),matched=accepted.reduce((s,e)=>s+e.w,0),total=selected.reduce((s,e)=>s+e.w,0),precision=Math.sqrt(err/Math.max(1e-8,weight));
 return {bpm:60/period,offset:mod(offset,period),coverage,matched:matched/total,jitter:precision,span,count:unique.size,score:coverage*Math.sqrt(matched/total)*Math.exp(-precision/.04)};
}
export function analyzePCM(samples,sr=8000){
 const duration=samples.length/sr,empty={bpm:null,offset:0,confidence:0,status:'insufficient',candidates:[],sections:[],duration};if(duration<8)return empty;
 const f=features(samples,sr),window=Math.min(28,duration),starts=duration<=window?[0]:[0,(duration-window)*.5,duration-window],sections=[];const candidates=[];
 for(const start of starts){const cs=correlationCandidates(f,start,start+window);const fits=[];for(const c of cs){for(let band=0;band<3;band++){const fit=fitGrid(f.events[band],c.bpm,start,start+window);if(fit)fits.push({...fit,band,seedStrength:c.strength})}}
 fits.sort((a,b)=>b.score-a.score);if(fits.length)sections.push({start,end:start+window,bpm:fits[0].bpm,score:fits[0].score});for(const fit of fits.slice(0,8))candidates.push(fit)}
 if(!candidates.length)return {...empty,sections};
 const refined=[];for(const seed of candidates.sort((a,b)=>b.score-a.score).slice(0,18)){for(const factor of [.5,1,2]){const bpm=seed.bpm*factor;if(bpm<40||bpm>240)continue;for(let band=0;band<3;band++){const fit=fitGrid(f.events[band],bpm,0,duration);if(!fit||fit.span<5)continue;const agreement=sections.filter(s=>Math.abs(s.bpm-fit.bpm)/fit.bpm<.015).length/Math.max(1,sections.length);refined.push({...fit,band,agreement,rank:fit.score*(.8+.2*agreement)})}}}
 refined.sort((a,b)=>b.rank-a.rank);const unique=[];for(const r of refined){if(!unique.some(x=>Math.abs(x.bpm-r.bpm)/r.bpm<.008))unique.push(r)}
 const best=unique[0];if(!best||best.coverage<.18||best.count<6||best.score<.27)return {...empty,sections};
 const alternatives=unique.filter(x=>x.rank>best.rank*.7).slice(1,4),ambiguous=alternatives.some(x=>Math.abs(x.bpm/best.bpm-2)<.03||Math.abs(x.bpm/best.bpm-.5)<.02);
 const informative=sections.filter(s=>s.score>=.25),same=s=>[.5,1,2].some(x=>Math.abs(s.bpm/best.bpm-x)<.025),stability=informative.length?informative.filter(same).length/informative.length:0,variable=informative.some(s=>s.score>=.3&&!same(s));
 const confidence=clamp(best.score*stability*(ambiguous?.7:1),0,1),status=variable||stability<.66?'variable':ambiguous?'ambiguous':confidence<.3?'low':'stable';
 return {bpm:Math.round(best.bpm*100)/100,offset:best.offset,confidence,status,jitterMs:Math.round(best.jitter*10000)/10,coverage:best.coverage,sections,candidates:unique.slice(0,4).map(x=>({bpm:Math.round(x.bpm*100)/100,score:Math.round(x.rank*100)/100})),duration,analyzedSeconds:duration};
}
// Transfer only an 8kHz analysis proxy, never another complete stereo PCM set.
let worker,sequence=0;const pending=new Map();
export async function estimateTempo(buffer){
 const sr=8000,length=Math.min(Math.floor(buffer.duration*sr),sr*900),pcm=new Float32Array(length);let channel=0,best=-1;
 for(let c=0;c<buffer.numberOfChannels;c++){const a=buffer.getChannelData(c);let energy=0;for(let i=0;i<a.length;i+=997)energy+=a[i]*a[i];if(energy>best){best=energy;channel=c}}
 const source=buffer.getChannelData(channel),ratio=buffer.sampleRate/sr;for(let begin=0;begin<length;begin+=sr*4){const end=Math.min(length,begin+sr*4);for(let i=begin;i<end;i++){const a=Math.floor(i*ratio),b=Math.min(source.length,Math.floor((i+1)*ratio));let sum=0;for(let j=a;j<b;j++)sum+=source[j];pcm[i]=sum/Math.max(1,b-a)}await new Promise(resolve=>setTimeout(resolve,0))}
 if(!worker){worker=new Worker(new URL('./tempo-analysis.js?v=19',import.meta.url),{type:'module'});worker.onmessage=({data})=>{const p=pending.get(data.id);if(!p)return;clearTimeout(p.timer);pending.delete(data.id);data.error?p.reject(Error(data.error)):p.resolve(data.result)};worker.onerror=()=>{for(const p of pending.values()){clearTimeout(p.timer);p.reject(Error('BPM 分析线程中断，请重试'))}pending.clear();worker.terminate();worker=null}}
 return new Promise((resolve,reject)=>{const id=++sequence,timer=setTimeout(()=>{pending.delete(id);reject(Error('BPM 分析超时，请重试或手动校准'))},60000);pending.set(id,{resolve,reject,timer});worker.postMessage({id,pcm,sr},[pcm.buffer])});
}
if(typeof document==='undefined'&&typeof self!=='undefined'&&typeof self.postMessage==='function')self.onmessage=({data})=>{try{self.postMessage({id:data.id,result:analyzePCM(data.pcm,data.sr)})}catch(error){self.postMessage({id:data.id,error:error.message})}};
