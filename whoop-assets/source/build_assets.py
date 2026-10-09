"""Build a complete conceptual WHOOP 5.0 web asset kit. Units: millimeters -> meters."""
import json,struct,base64,io,math,pathlib,sys
import numpy as np
from PIL import Image,ImageDraw,ImageFont
import primitives as P
ROOT=pathlib.Path(__file__).resolve().parent.parent
MATS=[('Strap_Fabric',[.10,.11,.12,1],0,.92),('Strap_Fibers',[.23,.24,.25,1],0,.94),('Housing_Matte',[.06,.067,.073,1],.12,.43),('Clasp_Metal',[.18,.20,.22,1],.8,.33),('Sensor_Glass',[.022,.032,.028,1],.15,.14),('Sensor_LED',[.12,.76,.24,1],0,.3),('PCB',[.04,.064,.05,1],.15,.65),('Chip',[.013,.017,.02,1],.1,.6),('Gold_Contacts',[.68,.48,.17,1],.85,.3),('Battery_Foil',[.58,.60,.64,1],.85,.32),('Haptics_Metal',[.40,.43,.45,1],.8,.4)]
P.materials=MATS
GROUPS={};current=None
def group(name):
 global current
 current=name;GROUPS[name]=[]
def box(name,center,half,r,mat):
 P.rounded_box(name,np.array(center,float),half,r,mat);GROUPS[current].append(len(P.meshes)-1)
def tube(name,paths,r,mat,sides=6):
 P.tubes(name,paths,r,mat,sides);GROUPS[current].append(len(P.meshes)-1)
def point(theta,z,off=0):
 p=P.ringpoint(theta,z,off);t=(theta+np.pi)%(2*np.pi)-np.pi
 # Woven band routes over the sensor's outside. The underside stays exposed.
 if abs(t)<.52:p[0]=40.9+off
 elif abs(t)<.86:
  u=(.86-abs(t))/.34;blend=u*u*(3-2*u);p[0]+=(40.9+off-p[0])*blend
 return p
group('Strap');v=[];f=[];K=32;N=224
cross=[]
for cx,cz,start in [(.28,11.35,0),(-.28,11.35,90),(-.28,-11.35,180),(.28,-11.35,270)]:
 for a in np.linspace(start,start+90,8,endpoint=False):
  t=np.deg2rad(a);cross.append((cx+.60*np.cos(t),cz+.60*np.sin(t)))
for t in np.linspace(0,2*np.pi,N,endpoint=False):
 for off,z in cross:v.append(point(t,z,off))
for i in range(N):
 for j in range(K):
  a=i*K+j;b=((i+1)%N)*K+j;c=((i+1)%N)*K+(j+1)%K;d=i*K+(j+1)%K;f.extend([[a,b,c],[a,c,d]])
P.add('Strap_Surface',v,f,0);GROUPS[current].append(len(P.meshes)-1)
paths=[]
for i in range(88):
 t=2*np.pi*i/88
 for j in range(12):
  z=-10.4+j*1.88
  paths.append([point(t+.024*np.sin(a),z+.78*np.cos(a),.91+.07*np.sin(2*a)) for a in np.linspace(0,2*np.pi,10,endpoint=False)])
tube('Strap_Knit_Relief',paths,.10,1,5)
tube('Strap_Edge_Stitching',[[point(t,z,.55) for t in np.linspace(0,2*np.pi,224,endpoint=False)] for z in [-11.65,11.65]],.22,1,6)

# External envelope: 34.7 mm (Y) x 24 mm (Z) x 10.6 mm (X).
group('Housing');box('Housing_OuterCover',[37.9,0,0],[2.4,17.35,12],2.35,2)
for z in [-11.25,11.25]:box('Housing_SideRail',[35,0,z],[2.2,15.5,.7],.65,2)
box('Housing_StatusLED',[37.0,12.5,11.93],[.6,.72,.10],.09,5)
group('Haptics');box('Haptics_LRA',[35.25,-9.2,0],[.8,3.2,4.0],.7,10)
box('Haptics_Flex',[35.18,-5.1,0],[.08,1.5,1.35],.07,8)
group('Mainboard');box('Mainboard_PCB',[34.65,0,0],[.32,14.7,10.0],.3,6)
for y,z,hy,hz in [(7,3,3.6,3.1),(-1,-3,3.4,3.2),(-9,4,2.3,2.2),(10,-6,1.5,1.4)]:
 box('Mainboard_Chip',[35.28,y,z],[.38,hy,hz],.3,7)
for i in range(22):
 y=-13+(i%11)*2.5;z=(-8.8 if i<11 else 8.8)
 box('Mainboard_Contact',[35.15,y,z],[.16,.45,.32],.14,8)
for i in range(16):
 y=-12+(i%8)*3.3;z=-6.8+(i//8)*12.8
 box('Mainboard_Component',[35.25,y,z],[.23,.57,.36],.18,9)
group('Battery');box('Battery_Cell',[33.15,1.6,0],[.8,9.1,6.5],.75,9)
box('Battery_Flex',[33.25,11.5,3.0],[.11,2.0,1.4],.1,8)
group('Sensors');box('Sensors_PCB',[31.7,0,0],[.28,13.8,9.8],.26,6)
for y,z,mat in [(8,0,5),(-8,0,5),(0,-4.7,4),(0,4.7,4),(0,0,4)]:
 box('Sensors_OpticalWindow',[31.03,y,z],[.36,2.0,1.8],.34,mat)
for z in [-8.7,8.7]:
 for y in [-11,-4,4,11]:box('Sensors_Contact',[31.28,y,z],[.12,.52,.36],.11,8)
group('Backplate');box('Backplate_InnerShell',[30.25,0,0],[.55,16.4,11.45],.54,2)
for y,z,mat in [(8,0,5),(-8,0,5),(0,-4.7,4),(0,4.7,4),(0,0,4)]:
 box('Backplate_OpticalGlass',[29.64,y,z],[.16,2,1.8],.15,mat)
group('Clasp');box('Clasp_Bridge',[40.85,-13.7,0],[.48,3.4,11.85],.45,3)
for y in [-17.1,17.1]:box('Clasp_Hinge',[31.2,y,0],[1.2,1.0,11.3],.9,3)
for y,z in [(-13.5,-2),(-14.3,-.6),(-13.5,.8),(-14.3,2.2)]:box('Clasp_ConceptMark',[41.4,y,z],[.06,1.0,.12],.05,9)

ORIGIN={k:np.array([34.3,0,0])*.001 for k in GROUPS};ORIGIN['Strap']=np.zeros(3);ORIGIN['Clasp']=np.array([31.2,-17.1,0])*.001
ORDER=['Housing','Haptics','Mainboard','Battery','Sensors','Backplate']
EXPLODE={k:np.zeros(3) for k in GROUPS}
for k,d in zip(ORDER,[.140,.084,.028,-.028,-.084,-.140]):EXPLODE[k]=np.array([0,0,d])
EXPLODE['Strap']=EXPLODE['Housing'].copy();EXPLODE['Clasp']=EXPLODE['Housing'].copy()

# Tileable grayscale woven PBR maps. GLB embeds all four texture PNGs.
S=512;y,x=np.mgrid[0:S,0:S];a=2*np.pi*x/64;b=2*np.pi*y/64
height=(.50+.23*np.sin(a)*np.cos(b)+.10*np.cos(2*a+b)+.08*np.sin(2*b-a))
base=np.clip(.63+.35*height,0,1);rgb=np.uint8(np.repeat(base[:,:,None],3,axis=2)*255)
Image.fromarray(rgb).save(ROOT/'model/textures/fabric-basecolor.png')
dy,dx=np.gradient(height);normal=np.stack([-dx*9,-dy*9,np.ones_like(dx)],axis=2);normal/=np.linalg.norm(normal,axis=2)[:,:,None]
Image.fromarray(np.uint8((normal*.5+.5)*255)).save(ROOT/'model/textures/fabric-normal.png')
mr=np.zeros((S,S,3),np.uint8);mr[:,:,0]=255;mr[:,:,1]=np.uint8(np.clip(.85+.12*height,0,1)*255)
Image.fromarray(mr).save(ROOT/'model/textures/fabric-metalrough.png')
Image.fromarray(np.uint8(np.repeat((.75+.25*height)[:,:,None],3,axis=2)*255)).save(ROOT/'model/textures/fabric-occlusion.png')

def export(path,mobile=False):
 d={'asset':{'version':'2.0','generator':'WHOOP 5.0 conceptual asset builder; approximate internal components'},'scene':0,'scenes':[{'nodes':[0]}],'nodes':[{'name':'WHOOP_Root','children':[]}],'meshes':[],'materials':[],'accessors':[],'bufferViews':[],'buffers':[{'byteLength':0}],'animations':[],'extras':{'units':'meters','external_envelope_mm':[34.7,24,10.6],'internal_layout':'illustrative','product':'WHOOP 5.0','default_variant':'graphite'}}
 buf=bytearray()
 def view(blob,target=None):
  while len(buf)%4:buf.append(0)
  i=len(d['bufferViews']);v={'buffer':0,'byteOffset':len(buf),'byteLength':len(blob)}
  if target:v['target']=target
  d['bufferViews'].append(v);buf.extend(blob);return i
 def acc(values,typ,comp,target=None):
  values=np.asarray(values,dtype=np.float32 if comp==5126 else np.uint32);bv=view(values.tobytes(),target);i=len(d['accessors']);o={'bufferView':bv,'componentType':comp,'count':len(values),'type':typ}
  if typ in ['VEC3','SCALAR']:o.update(min=np.min(values,axis=0).reshape(-1).tolist(),max=np.max(values,axis=0).reshape(-1).tolist())
  d['accessors'].append(o);return i
 d['images']=[];d['textures']=[];d['samplers']=[{'wrapS':10497,'wrapT':10497,'magFilter':9729,'minFilter':9987}]
 for f in ['fabric-basecolor.png','fabric-normal.png','fabric-metalrough.png','fabric-occlusion.png']:
  idx=len(d['images']);d['images'].append({'name':f,'bufferView':view((ROOT/'model/textures'/f).read_bytes()),'mimeType':'image/png'});d['textures'].append({'source':idx,'sampler':0})
 for name,col,metal,rough in MATS:
  m={'name':name,'pbrMetallicRoughness':{'baseColorFactor':col,'metallicFactor':metal,'roughnessFactor':rough},'doubleSided':True}
  if name=='Strap_Fabric':
   m['pbrMetallicRoughness']['baseColorTexture']={'index':0};m['pbrMetallicRoughness']['metallicRoughnessTexture']={'index':2};m['normalTexture']={'index':1,'scale':.55};m['occlusionTexture']={'index':3,'strength':.35}
  if name=='Sensor_LED':m['emissiveFactor']=[.035,.18,.025]
  d['materials'].append(m)
 groupidx={}
 for group,items in GROUPS.items():
  gi=len(d['nodes']);groupidx[group]=gi;d['nodes'][0]['children'].append(gi);d['nodes'].append({'name':group,'translation':ORIGIN[group].tolist(),'children':[],'extras':{'explode_delta':EXPLODE[group].tolist(),'internal_concept':group in ['Mainboard','Battery','Sensors','Haptics']}})
  for mi in items:
   m=P.meshes[mi]
   if mobile and m['name']=='Strap_Knit_Relief':continue
   if mobile and not m['name'].startswith('Strap_'):
    side=int(round(np.sqrt(len(m['v'])/6)))
    if side*side*6==len(m['v']):
     ids=np.unique(np.clip([0,2,5,side//2,side-6,side-3,side-1],0,side-1));newv=[];newn=[];newf=[];K=len(ids)
     for face in range(6):
      grid=np.arange(side*side).reshape(side,side)+face*side*side;keep=grid[np.ix_(ids,ids)].flatten();base=len(newv);newv.extend(m['v'][keep]);newn.extend(m['n'][keep])
      for u in range(K-1):
       for w in range(K-1):
        a=base+u*K+w;b=a+K;c=b+1;e=a+1;tri=[a,b,c]
        if np.dot(np.cross(np.array(newv[b])-newv[a],np.array(newv[c])-newv[a]),newn[a])<0:tri=[a,c,b];newf.extend([tri,[a,e,c]])
        else:newf.extend([tri,[a,c,e]])
     m=dict(m,v=np.array(newv,np.float32),n=np.array(newn,np.float32),f=np.array(newf,np.uint32))
   pos=m['v']-ORIGIN[group];attributes={'POSITION':acc(pos,'VEC3',5126,34962),'NORMAL':acc(m['n'],'VEC3',5126,34962)}
   if m['mat']==0:
    theta=np.arctan2(m['v'][:,1]/.036,m['v'][:,0]/.030);uv=np.c_[theta/(2*np.pi)*24,m['v'][:,2]/.023*4].astype(np.float32);attributes['TEXCOORD_0']=acc(uv,'VEC2',5126,34962)
   ii=acc(m['f'].flatten(),'SCALAR',5125,34963);meshindex=len(d['meshes']);d['meshes'].append({'name':m['name'],'primitives':[{'attributes':attributes,'indices':ii,'material':m['mat']}]});node=len(d['nodes']);d['nodes'].append({'name':m['name'],'mesh':meshindex});d['nodes'][gi]['children'].append(node)
 times=acc(np.array([0,2],np.float32),'SCALAR',5126);anim={'name':'WHOOP_Explode','samplers':[],'channels':[]}
 for name in GROUPS:
  if not np.any(EXPLODE[name]):continue
  out=acc(np.array([ORIGIN[name],ORIGIN[name]+EXPLODE[name]]),'VEC3',5126);si=len(anim['samplers']);anim['samplers'].append({'input':times,'output':out,'interpolation':'LINEAR'});anim['channels'].append({'sampler':si,'target':{'node':groupidx[name],'path':'translation'}})
 for name in ['Sensors','Backplate']:
  out=acc(np.array([[0,0,0,1],[0,1,0,0]]),'VEC4',5126);si=len(anim['samplers']);anim['samplers'].append({'input':times,'output':out,'interpolation':'LINEAR'});anim['channels'].append({'sampler':si,'target':{'node':groupidx[name],'path':'rotation'}})
 d['animations'].append(anim)
 angle=np.deg2rad(50);out=acc(np.array([[0,0,0,1],[0,0,np.sin(angle/2),np.cos(angle/2)]]),'VEC4',5126)
 d['animations'].append({'name':'WHOOP_ClaspOpen','samplers':[{'input':times,'output':out,'interpolation':'LINEAR'}],'channels':[{'sampler':0,'target':{'node':groupidx['Clasp'],'path':'rotation'}}]})
 d['buffers'][0]['byteLength']=len(buf);js=json.dumps(d,separators=(',',':')).encode();js+=b' '*((-len(js))%4);buf.extend(b'\0'*((-len(buf))%4));out=struct.pack('<III',0x46546c67,2,12+8+len(js)+8+len(buf))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(buf),0x004e4942)+buf;path.write_bytes(out)
 return d

VARIANTS=[{'id':'graphite','name':'Graphite','strap':'#202427','fiber':'#4b5155','clasp':'#535a60'},{'id':'dune','name':'Dune','strap':'#c4b397','fiber':'#e5d8bd','clasp':'#b7a88b'},{'id':'sage','name':'Sage','strap':'#718273','fiber':'#a5b3a4','clasp':'#7e8981'},{'id':'cobalt','name':'Cobalt','strap':'#335889','fiber':'#7393ba','clasp':'#707b87'}]
def hexcol(s):return np.array([int(s[i:i+2],16)/255 for i in [1,3,5]])
def colors(variant):
 cols=[np.array(m[1][:3]) for m in MATS]
 cols[0]=hexcol(variant['strap']);cols[1]=hexcol(variant['fiber']);cols[3]=hexcol(variant['clasp']);return cols
def render(path,variant=VARIANTS[0],yaw=-.62,pitch=.18,roll=-.18,W=1400,H=1100,explode=0,focus=None,label=None):
 canvas=np.zeros((H,W,3),np.float32);canvas[:]=[.075,.080,.085];depth=np.full((H,W),-np.inf,np.float32)
 c=np.cos;s=np.sin;RY=np.array([[c(yaw),0,s(yaw)],[0,1,0],[-s(yaw),0,c(yaw)]]);RX=np.array([[1,0,0],[0,c(pitch),-s(pitch)],[0,s(pitch),c(pitch)]]);RZ=np.array([[c(roll),-s(roll),0],[s(roll),c(roll),0],[0,0,1]]);R=RZ@RX@RY
 selected=[]
 for name,items in GROUPS.items():
  if focus and name!=focus:continue
  if not explode and not focus and name in ['Mainboard','Battery','Sensors','Haptics']:continue
  for i in items:
   if explode and name in ['Strap','Clasp']:continue
   source=P.meshes[i]
   if explode and name in ['Sensors','Backplate']:
    source=dict(source);q=np.diag([-1,1,-1]);source['v']=(source['v']-ORIGIN[name])@q+ORIGIN[name];source['n']=source['n']@q
   selected.append((source,EXPLODE[name]*explode))
 vv=np.concatenate([m['v']+off for m,off in selected])@R.T;center=(vv.min(axis=0)+vv.max(axis=0))/2;size=vv.max(axis=0)-vv.min(axis=0);scale=min(W*.84/max(size[0],.001),H*.75/max(size[1],.001));cols=colors(variant)
 light=np.array([-.5,.8,1.]);light/=np.linalg.norm(light)
 for m,off in selected:
  v=(m['v']+off)@R.T-center;n=m['n']@R.T;screen=np.c_[W/2+v[:,0]*scale,H/2-v[:,1]*scale];lam=np.maximum(n@light,0);rim=np.maximum(n@np.array([.9,.1,.35]),0);color=cols[m['mat']][None,:]*(.30+.8*lam[:,None]+.27*rim[:,None]);color+=np.maximum(n@np.array([-.12,.4,.908]),0)[:,None]**(30 if m['mat'] in [3,9,10] else 65)*(.25 if m['mat'] in [3,9,10] else .08)
  drawfaces=m['f']
  if m['name']=='Strap_Knit_Relief':drawfaces=drawfaces.reshape(-1,100,3)[::2].reshape(-1,3)
  for face in drawfaces:
   p=screen[face];mn=np.maximum(np.floor(p.min(axis=0)).astype(int),0);mx=np.minimum(np.ceil(p.max(axis=0)).astype(int),[W-1,H-1])
   if np.any(mx<mn):continue
   den=(p[1,1]-p[2,1])*(p[0,0]-p[2,0])+(p[2,0]-p[1,0])*(p[0,1]-p[2,1])
   if abs(den)<1e-8:continue
   x,y=np.meshgrid(np.arange(mn[0],mx[0]+1)+.5,np.arange(mn[1],mx[1]+1)+.5);a=((p[1,1]-p[2,1])*(x-p[2,0])+(p[2,0]-p[1,0])*(y-p[2,1]))/den;b=((p[2,1]-p[0,1])*(x-p[2,0])+(p[0,0]-p[2,0])*(y-p[2,1]))/den;c1=1-a-b;z=a*v[face[0],2]+b*v[face[1],2]+c1*v[face[2],2];region=depth[mn[1]:mx[1]+1,mn[0]:mx[0]+1];mask=(a>=0)&(b>=0)&(c1>=0)&(z>region);region[mask]=z[mask];col=a[:,:,None]*color[face[0]]+b[:,:,None]*color[face[1]]+c1[:,:,None]*color[face[2]];canvas[mn[1]:mx[1]+1,mn[0]:mx[0]+1][mask]=col[mask]
 img=Image.fromarray(np.uint8(np.clip(canvas,0,1)**.7*255))
 if label:
  dr=ImageDraw.Draw(img);dr.text((32,28),label,fill=(221,226,230));dr.text((32,H-32),'CONCEPT RECONSTRUCTION / INTERNALS ILLUSTRATIVE',fill=(159,169,175))
 img.save(path)

if __name__=='__main__':
 web=export(ROOT/'model/whoop-web.glb');mobile=export(ROOT/'model/whoop-mobile.glb',True)
 # Uncompressed editable source independent of a particular modelling app.
 np.savez(ROOT/'model/whoop-source.npz',**{f'{i}_{k}':m[k] for i,m in enumerate(P.meshes) for k in ['v','n','f']})
 manifest={'units':'meters','product':'WHOOP 5.0','groups':{},'meshes':[]}
 for name,ids in GROUPS.items():manifest['groups'][name]={'origin':ORIGIN[name].tolist(),'explode_delta':EXPLODE[name].tolist(),'parts':[P.meshes[i]['name'] for i in ids]}
 for i,m in enumerate(P.meshes):manifest['meshes'].append({'array_prefix':str(i),'name':m['name'],'material':MATS[m['mat']][0]})
 (ROOT/'model/source-manifest.json').write_text(json.dumps(manifest,indent=2))
 (ROOT/'variants/variants.json').write_text(json.dumps({'status':'concept colors, not official SKUs','shared_model':'../model/whoop-web.glb','variants':VARIANTS},indent=2))
 print('Models and editable geometry written',flush=True)
 for variant in VARIANTS:
  dr=ROOT/'variants'/variant['id'];dr.mkdir(exist_ok=True);render(dr/'front.png',variant,label='WHOOP 5.0 / '+variant['name'].upper());render(dr/'back-sensor.png',variant,yaw=1.15,pitch=-.05,roll=.1,W=1000,H=850,label='SENSOR SIDE / '+variant['name'].upper());(dr/'variant.json').write_text(json.dumps(variant,indent=2));print('Rendered',variant['id'],flush=True)
 render(ROOT/'renders/01-hero.png',label='WHOOP 5.0 / SCREENLESS BY DESIGN')
 render(ROOT/'renders/02-side-profile.png',yaw=.15,pitch=.06,roll=-.14,label='COMPACT SENSOR / 34.7 x 24 x 10.6 MM')
 render(ROOT/'renders/03-sensors.png',yaw=1.12,pitch=-.05,focus='Sensors',label='OPTICAL SENSOR ARRAY / CONCEPT LAYOUT')
 render(ROOT/'renders/04-woven-band.png',VARIANTS[1],yaw=-.5,pitch=.45,roll=.17,focus='Strap',label='WOVEN BAND / DUNE CONCEPT')
 render(ROOT/'renders/05-exploded.png',yaw=-1.15,pitch=.10,roll=0,W=2000,H=1000,explode=1,label='HOUSING / HAPTICS / MAINBOARD / BATTERY / SENSORS / BACKPLATE')
 for name in ORDER:render(ROOT/'renders'/('part-'+name.lower()+'.png'),yaw=1.25 if name in ['Sensors','Backplate'] else -1.25,pitch=.07,roll=0,W=700,H=700,focus=name,label=name.upper())
 print('All renders complete',flush=True)
