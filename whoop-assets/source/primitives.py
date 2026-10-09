"""Procedural WHOOP-like reference reconstruction. Python, NumPy, Pillow only."""
import numpy as np, json, struct, math, pathlib, base64
from PIL import Image, ImageDraw, ImageFont
ROOT=pathlib.Path(__file__).resolve().parent
meshes=[]
materials=[('Woven strap',[.49,.51,.52,1],0,.95),('Raised woven fibers',[.68,.70,.71,1],0,.96),('Ceramic silver housing',[.81,.83,.84,1],.28,.31),('Brushed clasp',[.57,.60,.62,1],.65,.4),('Sensor glass',[.055,.064,.069,1],.15,.21),('Sensor LEDs',[.07,.63,.3,1],.05,.3),('Engraved details',[.26,.28,.29,1],.5,.4)]
def add(name,v,f,mat,n=None):
 v=np.asarray(v,dtype=np.float32);f=np.asarray(f,dtype=np.uint32)
 if n is None:
  n=np.zeros_like(v);fn=np.cross(v[f[:,1]]-v[f[:,0]],v[f[:,2]]-v[f[:,0]])
  for i in range(3):np.add.at(n,f[:,i],fn)
  n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-10)
 meshes.append(dict(name=name,v=v*.001,f=f,n=np.asarray(n,np.float32),mat=mat))
def rounded_box(name,center,half,r,mat):
 verts=[];norms=[];faces=[];half=np.array(half)
 # Six independently parameterized rounded faces, with dense bevel sampling.
 for ax in range(3):
  others=[j for j in range(3) if j!=ax]
  coords=[]
  for j in others:
   h=half[j];coords.append(np.unique(np.r_[np.linspace(-h,-h+r,7),np.linspace(-h+r,h-r,8),np.linspace(h-r,h,7)]))
  for sign in [-1,1]:
   base=len(verts);A,B=coords
   for a in A:
    for b in B:
     p=np.zeros(3);p[ax]=sign*half[ax];p[others]=[a,b]
     q=np.clip(p,-half+r,half-r);d=p-q;d/=np.linalg.norm(d)
     verts.append(q+d*r+center);norms.append(d)
   for i in range(len(A)-1):
    for j in range(len(B)-1):
     k=base+i*len(B)+j;quad=[k,k+len(B),k+len(B)+1,k+1]
     cross=np.cross(np.array(verts[quad[1]])-verts[quad[0]],np.array(verts[quad[2]])-verts[quad[0]])
     if cross[ax]*sign<0:quad.reverse()
     faces.extend([[quad[0],quad[1],quad[2]],[quad[0],quad[2],quad[3]]])
 add(name,verts,faces,mat,norms)
def ringpoint(theta,z,offset=0):
 normal=np.array([np.cos(theta)/30,np.sin(theta)/36,0]);normal/=np.linalg.norm(normal)
 return np.array([30*np.cos(theta),36*np.sin(theta),z])+normal*offset
def strap():
 cross=[]
 for cx,cz,start in [(.25,11.5,0),(-.25,11.5,90),(-.25,-11.5,180),(.25,-11.5,270)]:
  for a in np.linspace(start,start+90,9,endpoint=False):
   t=np.deg2rad(a);cross.append((cx+.65*np.cos(t),cz+.65*np.sin(t)))
 v=[];f=[];N=320;K=len(cross)
 for t in np.linspace(0,2*np.pi,N,endpoint=False):
  for off,z in cross:v.append(ringpoint(t,z,off))
 for i in range(N):
  for j in range(K):
   a=i*K+j;b=((i+1)%N)*K+j;c=((i+1)%N)*K+(j+1)%K;d=i*K+(j+1)%K
   f.extend([[a,b,c],[a,c,d]])
 # Cross-section order above is counterclockwise viewed tangentially.
 add('Continuous elliptical woven strap',v,f,0)
def tubes(name,paths,r,mat,sides=5):
 verts=[];norms=[];faces=[]
 for path in paths:
  path=np.array(path);base=len(verts);M=len(path)
  tangent=np.roll(path,-1,axis=0)-np.roll(path,1,axis=0);tangent/=np.linalg.norm(tangent,axis=1)[:,None]
  radial=np.copy(path);radial[:,2]=0;radial/=np.linalg.norm(radial,axis=1)[:,None]
  u=np.cross(tangent,radial);u/=np.linalg.norm(u,axis=1)[:,None];w=np.cross(tangent,u)
  for k,p in enumerate(path):
   for a in np.linspace(0,2*np.pi,sides,endpoint=False):
    n=u[k]*np.cos(a)+w[k]*np.sin(a);verts.append(p+r*n);norms.append(n)
  for k in range(M):
   for j in range(sides):
    a=base+k*sides+j;b=base+((k+1)%M)*sides+j;c=base+((k+1)%M)*sides+(j+1)%sides;d=base+k*sides+(j+1)%sides
    faces.extend([[a,b,c],[a,c,d]])
 add(name,verts,faces,mat,norms)