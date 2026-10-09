// ES module. Assumes your existing application has installed Three.js.
// Pass one GLTFLoader instance to loadWhoop(). Load the shared model once.
import * as THREE from 'three';

export const requiredGroups = ['Strap','Clasp','Housing','Haptics','Mainboard','Battery','Sensors','Backplate'];
export const conceptVariants = [
  { id:'graphite', name:'Graphite', strap:'#202427', fiber:'#4b5155', clasp:'#535a60' },
  { id:'dune', name:'Dune', strap:'#c4b397', fiber:'#e5d8bd', clasp:'#b7a88b' },
  { id:'sage', name:'Sage', strap:'#718273', fiber:'#a5b3a4', clasp:'#7e8981' },
  { id:'cobalt', name:'Cobalt', strap:'#335889', fiber:'#7393ba', clasp:'#707b87' }
];

export async function loadWhoop(loader, url='./model/whoop-web.glb') {
  const gltf = await loader.loadAsync(url);
  for (const name of requiredGroups) {
    if (!gltf.scene.getObjectByName(name)) throw new Error(`WHOOP group missing: ${name}`);
  }
  return gltf;
}

export function createVariant(sharedScene, variant) {
  const root=sharedScene.clone(true);
  // clone(true) shares mesh materials: detach them before changing one variant.
  const detached=new Map();
  root.traverse(node => {
    if (!node.isMesh) return;
    const detach=material => {
      if (!detached.has(material.uuid)) detached.set(material.uuid, material.clone());
      return detached.get(material.uuid);
    };
    node.material=Array.isArray(node.material)?node.material.map(detach):detach(node.material);
  });
  const colors={Strap_Fabric:variant.strap,Strap_Fibers:variant.fiber,Clasp_Metal:variant.clasp};
  root.traverse(node => {
    if (!node.isMesh) return;
    const materials=Array.isArray(node.material)?node.material:[node.material];
    materials.forEach(m => { if(colors[m.name]) m.color.set(colors[m.name]); });
  });
  root.userData.variant=variant.id;
  root.userData.whoopRest={};
  for (const name of requiredGroups) {
    const node=root.getObjectByName(name);
    root.userData.whoopRest[name]={position:node.position.clone(),quaternion:node.quaternion.clone()};
  }
  return root;
}

export function setExplosion(root, progress, { hideBand=true }={}) {
  const p=THREE.MathUtils.clamp(progress,0,1);
  for(const name of requiredGroups) {
    const node=root.getObjectByName(name),rest=root.userData.whoopRest?.[name];
    if(!node||!rest) throw new Error('Call createVariant() before setExplosion().');
    const d=node.userData.explode_delta||[0,0,0];
    node.position.copy(rest.position).add(new THREE.Vector3(...d).multiplyScalar(p));
    if(name==='Sensors'||name==='Backplate') {
      node.quaternion.copy(rest.quaternion).multiply(new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0,1,0),Math.PI*p));
    }
    if(name==='Strap'||name==='Clasp') node.visible=!hideBand||p<0.10;
  }
}

export function setClaspOpen(root, progress) {
  const node=root.getObjectByName('Clasp'),rest=root.userData.whoopRest?.Clasp;
  if(!node||!rest) throw new Error('Call createVariant() before setClaspOpen().');
  const angle=THREE.MathUtils.clamp(progress,0,1)*THREE.MathUtils.degToRad(50);
  node.quaternion.copy(rest.quaternion).multiply(new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0,0,1),angle));
}

export function resetWhoop(root) {
  for(const name of requiredGroups) {
    const node=root.getObjectByName(name),rest=root.userData.whoopRest[name];
    node.position.copy(rest.position);node.quaternion.copy(rest.quaternion);node.visible=true;
  }
}

// Example:
// const gltf=await loadWhoop(loader);
// const products=conceptVariants.map(v=>createVariant(gltf.scene,v));
// products.forEach((p,i)=>{p.position.set((i-1.5)*0.11,0,0);scene.add(p)});
// setExplosion(products[0], scrollProgress);
// Alternatively use AnimationMixer with WHOOP_Explode or WHOOP_ClaspOpen clips.
// Choose the manual path OR the clip path for the same transforms.
