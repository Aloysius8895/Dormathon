from pathlib import Path
import base64,json
ROOT=Path(__file__).resolve().parent.parent
html=(ROOT/'source/viewer_template.html').read_text()
html=html.replace('WHOOP 3D 模型预览','WHOOP 5.0 素材预览').replace('REFERENCE RECONSTRUCTION · V1','WHOOP 5.0 · ASSET KIT').replace('WHOOP / 3D 模型','WHOOP 5.0 / Concept').replace('灰白机身 · 编织织带 · GLB 格式','四套配色 · 编织材质 · 六组拆解')
html=html.replace('<aside>','<div id="variants" style="position:absolute;top:115px;left:32px;display:flex;gap:7px"></div><div style="position:absolute;bottom:140px;left:50%;transform:translateX(-50%);text-align:center;max-width:90vw"><label>拆解 <input id="explode" type="range" min="0" max="1" step="0.01" value="0" style="width:170px;vertical-align:middle"></label><label style="margin-left:14px">扣具 <input id="clasp" type="range" min="0" max="1" step="0.01" value="0" style="width:90px;vertical-align:middle"></label><p id="parts" style="margin-top:12px;font-size:11px;line-height:1.8">内部结构为概念示意</p></div><aside>')
html=html.replace('WHOOP_Reference_Model.glb','whoop-web.glb')
html=html.replace('uniform float aspect;','uniform float aspect;uniform vec3 translation;uniform mat3 localRotation;uniform float centerX;')
html=html.replace('vec3 p=rotation*position;n=rotation*normal;','vec3 world=localRotation*position+translation;world.x-=centerX;vec3 p=rotation*world;n=rotation*localRotation*normal;')
html=html.replace("['rotation','distance','aspect','color','metal','rough']","['rotation','distance','aspect','color','metal','rough','translation','localRotation','centerX']")
start=html.index('let parts=[];for(let mesh of doc.meshes)')
end=html.index('let yaw=',start)
loader="""let parts=[];let groupInfo={};for(let node of doc.nodes){if(node.children&&node.name!=='WHOOP_Root'){groupInfo[node.name]=node;for(let ni of node.children){let child=doc.nodes[ni];if(child.mesh===undefined)continue;let mesh=doc.meshes[child.mesh];for(let p of mesh.primitives){const idx=readAccess(p.indices);parts.push({group:node.name,pos:buffer(gl.ARRAY_BUFFER,readAccess(p.attributes.POSITION)),norm:buffer(gl.ARRAY_BUFFER,readAccess(p.attributes.NORMAL)),idx:buffer(gl.ELEMENT_ARRAY_BUFFER,idx),count:idx.length,mat:doc.materials[p.material].pbrMetallicRoughness,materialName:doc.materials[p.material].name})}}}}\n"""
html=html[:start]+loader+html[end:]
html=html.replace('yaw=.56,pitch=.22,roll=-.21,dist=.17','yaw=-.62,pitch=.18,roll=-.18,dist=.18')
html=html.replace('yaw=.56;pitch=.22;roll=-.21;dist=innerWidth<600?.23:.17','yaw=-.62;pitch=.18;roll=-.18;dist=innerWidth<600?.23:.18;document.getElementById(\'explode\').value=0;document.getElementById(\'clasp\').value=0')
html=html.replace('gl.uniform1f(un.distance,dist);','const ex=Number(document.getElementById(\'explode\').value),cl=Number(document.getElementById(\'clasp\').value);let dd=dist+ex*.43;gl.uniform1f(un.distance,dd);gl.uniform1f(un.centerX,.004);document.getElementById(\'parts\').textContent=ex>.1?\'Housing · Haptics · Mainboard · Battery · Sensors · Backplate / 概念结构\':\'内部结构为概念示意\';')
html=html.replace('for(let p of parts){gl.bindBuffer','for(let p of parts){if(ex>.1&&(p.group===\'Strap\'||p.group===\'Clasp\'))continue;let g=groupInfo[p.group];gl.uniform3fv(un.translation,g.translation.map((n,i)=>n+(g.extras.explode_delta[i]*ex)));let an=p.group===\'Clasp\'?cl*Math.PI*50/180:0;gl.uniformMatrix3fv(un.localRotation,false,[Math.cos(an),Math.sin(an),0,-Math.sin(an),Math.cos(an),0,0,0,1]);gl.bindBuffer')
html=html.replace('gl.uniform3fv(un.color,p.mat.baseColorFactor.slice(0,3));','gl.uniform3fv(un.color,variantColors[p.materialName]||p.mat.baseColorFactor.slice(0,3));')
html=html.replace("gl.bindBuffer(gl.ARRAY_BUFFER,p.pos);","if(p.group==='Sensors'||p.group==='Backplate'){let ay=ex*Math.PI;gl.uniformMatrix3fv(un.localRotation,false,[Math.cos(ay),0,-Math.sin(ay),0,1,0,Math.sin(ay),0,Math.cos(ay)])}gl.bindBuffer(gl.ARRAY_BUFFER,p.pos);")
variants=json.loads((ROOT/'variants/variants.json').read_text())['variants']
setup="const variants="+json.dumps(variants)+";let variantColors={};function rgb(h){return [1,3,5].map(i=>parseInt(h.slice(i,i+2),16)/255)}function setVariant(v){variantColors={Strap_Fabric:rgb(v.strap),Strap_Fibers:rgb(v.fiber),Clasp_Metal:rgb(v.clasp)};for(let b of document.getElementById('variants').children)b.style.outline=b.dataset.id===v.id?'1px solid #c4ee9a':'none'}for(let v of variants){let b=document.createElement('button');b.textContent=v.name;b.dataset.id=v.id;b.title='概念配色';b.onclick=()=>setVariant(v);document.getElementById('variants').appendChild(b)}setVariant(variants[0]);\n"
html=html.replace('let yaw=',setup+'let yaw=')
html=html.replace("const encoded='__GLB_BASE64__'","const encoded='"+base64.b64encode((ROOT/'model/whoop-web.glb').read_bytes()).decode()+"'")
(ROOT/'preview/WHOOP_Assets_Preview.html').write_text(html)
print('Offline preview generated')
