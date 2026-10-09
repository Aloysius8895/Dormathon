// Puts the WHOOP model inside the original FS 60P WebGL scene.
//
// The original page animates the node "theWatch" and its parts with GSAP
// timelines (intro spin, presentation, disassembly, hover/click zoom,
// long-press explode, bracelet links, footer colour picker). Instead of drawing
// WHOOP on a second canvas, this module loads WHOOP with the page's own
// Three.js (r162) GLTFLoader, parents it to "theWatch" and copies each watch
// part's animated offset onto the matching WHOOP group every frame. The watch
// meshes stay in the scene, so the page's raycast boxes, timelines and labels
// keep working, but they move to a layer the camera does not render.

const HIDDEN_LAYER = 7;
const MODEL_URL = { full: '/whoop/model/whoop-web.glb', light: '/whoop/model/whoop-mobile.glb' };

// Watch disassembly layers, back (skin side) to front, paired with WHOOP
// groups in the same stacking order.
const PART_PAIRS = [
  ['xploded-9', 'Backplate'],
  ['xploded-10', 'Sensors'],
  ['xploded-28', 'Battery'],
  ['xploded-29', 'Mainboard'],
  ['xploded-42', 'Haptics'],
  ['xploded-45', 'Housing'],
];
const BAND_GROUPS = ['Strap', 'Clasp'];

// Original colour configs, in page order, mapped to the WHOOP concept colours.
const CONFIG_VARIANTS = {
  first: { id: 'graphite', strap: '#202427', fiber: '#4b5155', clasp: '#535a60' },
  second: { id: 'dune', strap: '#c4b397', fiber: '#e5d8bd', clasp: '#b7a88b' },
  third: { id: 'sage', strap: '#718273', fiber: '#a5b3a4', clasp: '#7e8981' },
  fourth: { id: 'cobalt', strap: '#335889', fiber: '#7393ba', clasp: '#707b87' },
};
const VARIANT_MATERIALS = { Strap_Fabric: 'strap', Strap_Fibers: 'fiber', Clasp_Metal: 'clasp' };

// WHOOP: band loop in XY, sensor stack along +X (skin side at low X).
// Watch: dial faces +Z, bracelet runs along Y. Rotating -90 deg about Y maps
// WHOOP +X onto watch +Z, so both models explode along the same axis.
const WHOOP_YAW = -Math.PI / 2;
// Scale WHOOP so its sensor spans the watch case's width.
const CASE_FILL = 1.0;

// The page lights its scene only with an environment map and gives its own
// watch materials envMapIntensity up to 5 plus an additive env map. Plain
// glTF materials need the same boost, or the concept colours render near black.
const ENV_INTENSITY = 5;

// The page's single bracelet link (metres): 5.8 mm pitch, 18.6 mm wide.
const LINK_PITCH = 0.0058;
const LINK_WIDTH = 0.0186;
const BAND_WIDTH = 0.024;

const state = {
  project: null,
  anchor: null,
  oriented: null,
  links: [],
  band: null,
  materials: [],
  targetColors: CONFIG_VARIANTS.first,
  // The page sets its store's current config to "first" when it attaches.
  config: 'first',
  lastTime: 0,
};

function nextFrame() {
  return new Promise(resolve => requestAnimationFrame(resolve));
}

async function waitFor(read, label, timeout = 120000) {
  const start = performance.now();
  for (;;) {
    const value = read();
    if (value) return value;
    if (performance.now() - start > timeout) throw new Error(`Timed out waiting for ${label}`);
    await nextFrame();
  }
}

// Import the page module the router already loaded, so we get the same
// project instance rather than a second copy.
async function loadProject() {
  const entry = await waitFor(
    () => performance.getEntriesByType('resource').find(item => /\/assets\/the-watch\.[^/]+\.js$/.test(item.name)),
    'the-watch module',
  );
  const module = await import(/* @vite-ignore */ entry.name);
  return module.project;
}

function loadWhoop(project, url) {
  const GLTFLoader = project.assetsManager.loaders.models.loader.constructor;
  return new GLTFLoader().loadAsync(url).then(gltf => {
    for (const name of [...PART_PAIRS.map(([, group]) => group), ...BAND_GROUPS]) {
      if (!gltf.scene.getObjectByName(name)) throw new Error(`WHOOP group missing: ${name}`);
    }
    return gltf.scene;
  });
}

function hideOriginalMeshes(root, keep) {
  root.traverse(node => {
    if (keep.has(node)) return;
    if (!node.isMesh && !node.isLine && !node.isPoints) return;
    // Invisible raycast boxes must stay on the default layer to remain clickable.
    if (node.material && !Array.isArray(node.material) && node.material.visible === false) return;
    node.layers.set(HIDDEN_LAYER);
  });
}

function restoreLayers(root) {
  root?.traverse(node => {
    if (node.layers.isEnabled(HIDDEN_LAYER)) node.layers.set(0);
  });
}

function keepSet(scene) {
  const keep = new Set();
  if (scene.laserBeam) keep.add(scene.laserBeam);
  if (state.anchor) state.anchor.traverse(node => keep.add(node));
  return keep;
}

// Bounds of an object's meshes in `frame`'s local space, without needing Box3.
function boundsIn(object, frame) {
  const V = frame.position.constructor;
  const M = frame.matrixWorld.constructor;
  const inverse = new M().copy(frame.matrixWorld).invert();
  const min = new V(Infinity, Infinity, Infinity);
  const max = new V(-Infinity, -Infinity, -Infinity);
  const corner = new V();
  object.updateWorldMatrix(true, true);
  object.traverse(node => {
    if (!node.isMesh) return;
    if (!node.geometry.boundingBox) node.geometry.computeBoundingBox();
    const box = node.geometry.boundingBox;
    const toFrame = new M().multiplyMatrices(inverse, node.matrixWorld);
    for (let i = 0; i < 8; i++) {
      corner.set(i & 1 ? box.max.x : box.min.x, i & 2 ? box.max.y : box.min.y, i & 4 ? box.max.z : box.min.z).applyMatrix4(toFrame);
      min.min(corner);
      max.max(corner);
    }
  });
  return { min, max, center: min.clone().add(max).multiplyScalar(0.5), size: max.clone().sub(min) };
}

function cloneMaterials(root) {
  const cloned = new Map();
  const detach = material => {
    if (!cloned.has(material)) {
      const copy = material.clone();
      copy.envMapIntensity = ENV_INTENSITY;
      cloned.set(material, copy);
    }
    return cloned.get(material);
  };
  root.traverse(node => {
    if (!node.isMesh) return;
    node.material = Array.isArray(node.material) ? node.material.map(detach) : detach(node.material);
  });
  return [...cloned.values()];
}

function variantMaterials(materials) {
  return materials.filter(material => VARIANT_MATERIALS[material.name]);
}

function paint(materials, variant) {
  for (const material of variantMaterials(materials)) material.color.set(variant[VARIANT_MATERIALS[material.name]]);
}

// Build the WHOOP anchor in watch-local space: rotate, then scale and centre
// the sensor on the watch case.
function buildAnchor(watch, parts, whoopScene) {
  const Object3D = watch.constructor;
  const anchor = new Object3D();
  anchor.name = 'WHOOP_Anchor';
  watch.add(anchor);
  anchor.updateWorldMatrix(true, false);

  const oriented = new Object3D();
  oriented.rotation.y = WHOOP_YAW;
  oriented.add(whoopScene);
  anchor.add(oriented);

  const device = new Object3D();
  for (const [, name] of PART_PAIRS) device.add(whoopScene.getObjectByName(name).clone());
  oriented.add(device);
  const deviceBox = boundsIn(device, anchor);
  oriented.remove(device);

  const caseBox = boundsIn(parts.emptyXploded, anchor);
  const scale = CASE_FILL * Math.max(caseBox.size.x, caseBox.size.y) / Math.max(deviceBox.size.x, deviceBox.size.y);
  oriented.scale.setScalar(scale);
  oriented.position.copy(caseBox.center).sub(deviceBox.center.clone().multiplyScalar(scale));
  anchor.updateWorldMatrix(false, true);
  state.oriented = oriented;
  return anchor;
}

// Wrap a WHOOP group in a pivot at its own centre (watch-local), so part
// rotations from the page spin each group in place.
function pivotFor(anchor, group) {
  const pivot = new anchor.constructor();
  pivot.name = `${group.name}_Pivot`;
  pivot.position.copy(boundsIn(group, anchor).center);
  anchor.add(pivot);
  pivot.updateWorldMatrix(false, false);
  pivot.attach(group);
  return { pivot, rest: pivot.position.clone() };
}

function visibleInWatch(node, watch) {
  for (let current = node; current && current !== watch; current = current.parent) if (!current.visible) return false;
  return true;
}

function attachWhoop(project, whoopScene) {
  const scene = project.webgl.scene;
  const watch = scene.watch;
  const parts = scene.watchParts;

  state.materials = cloneMaterials(whoopScene);
  paint(state.materials, state.targetColors);
  const anchor = buildAnchor(watch, parts, whoopScene);
  state.anchor = anchor;

  state.links = PART_PAIRS.map(([watchName, whoopName]) => {
    const part = parts.horizontal.find(item => item.name === watchName);
    if (!part) throw new Error(`Watch part missing: ${watchName}`);
    return { part, ...pivotFor(anchor, whoopScene.getObjectByName(whoopName)) };
  });
  const bandPivot = new anchor.constructor();
  bandPivot.name = 'Band_Pivot';
  anchor.add(bandPivot);
  for (const name of BAND_GROUPS) bandPivot.attach(whoopScene.getObjectByName(name));
  state.band = { pivot: bandPivot, source: parts.emptyStrap, rest: parts.emptyStrap.position.clone() };

  hideOriginalMeshes(watch, keepSet(scene));

  project.state.on(project.events.CONFIG_CHANGE, ({ configName = 'first', duration = 1 } = {}) => {
    const variant = CONFIG_VARIANTS[configName];
    if (!variant) return;
    state.config = configName;
    state.targetColors = variant;
    if (!duration) paint(state.materials, variant);
    document.body.dataset.whoopVariant = variant.id;
  });
  document.body.dataset.whoopVariant = state.targetColors.id;

  const previous = scene.onBeforeRender;
  scene.onBeforeRender = function (...args) {
    previous.apply(this, args);
    sync(watch);
  };
  sync(watch);
}

// The footer shows four small cloned watches, one per colour config. Replace
// each clone's meshes with a lighter WHOOP in that config's colours.
function addFooterWhoops(scene, lightScene) {
  const group = scene.watchesGroup?.watchesInsideGroup;
  if (!group) return;
  const Object3D = scene.watch.constructor;
  group.children.forEach(wrapper => {
    const clone = wrapper.children[0];
    const variant = CONFIG_VARIANTS[clone?.userData.config];
    if (!variant) return;
    hideOriginalMeshes(clone, new Set());
    const anchor = new Object3D();
    anchor.name = 'WHOOP_Anchor';
    const oriented = new Object3D();
    oriented.position.copy(state.oriented.position);
    oriented.quaternion.copy(state.oriented.quaternion);
    oriented.scale.copy(state.oriented.scale);
    const copy = lightScene.clone(true);
    paint(cloneMaterials(copy), variant);
    oriented.add(copy);
    anchor.add(oriented);
    clone.add(anchor);
  });
}

// Cut one link-length piece from the far side of the WHOOP band loop, where
// it runs straight, and lay it out like the page's bracelet link: pitch along
// X, width along Y, outer face towards +Z.
function buildBandSegment(whoopScene, constructors) {
  const scale = LINK_WIDTH / BAND_WIDTH;
  const halfPitch = LINK_PITCH / scale / 2;
  const sources = ['Strap_Surface', 'Strap_Knit_Relief'].map(name => whoopScene.getObjectByName(name)).filter(Boolean);
  const positions = [];
  const normals = [];
  const uvs = [];
  const groups = [];
  const materials = [];
  for (const mesh of sources) {
    const { position, normal, uv } = mesh.geometry.attributes;
    const index = mesh.geometry.index;
    const vertex = i => (index ? index.getX(i) : i);
    const count = index ? index.count : position.count;
    const start = positions.length / 3;
    for (let t = 0; t < count; t += 3) {
      const ids = [vertex(t), vertex(t + 1), vertex(t + 2)];
      const x = ids.reduce((sum, i) => sum + position.getX(i), 0) / 3;
      const y = ids.reduce((sum, i) => sum + position.getY(i), 0) / 3;
      if (x > -0.02 || Math.abs(y) > halfPitch) continue;
      for (const i of ids) {
        // (x, y, z) -> (-y, z, -x): a proper rotation, so winding is kept.
        positions.push(-position.getY(i) * scale, position.getZ(i) * scale, -position.getX(i) * scale);
        normals.push(-normal.getY(i), normal.getZ(i), -normal.getX(i));
        uvs.push(uv ? uv.getX(i) : 0, uv ? uv.getY(i) : 0);
      }
    }
    if (positions.length / 3 > start) {
      groups.push({ start, count: positions.length / 3 - start, materialIndex: materials.length });
      // Use the colour-synced copy of the material so config changes apply.
      materials.push(state.materials.find(material => material.name === mesh.material.name) || mesh.material);
    }
  }
  if (!groups.length) return null;

  let minZ = Infinity;
  let maxZ = -Infinity;
  for (let i = 2; i < positions.length; i += 3) {
    minZ = Math.min(minZ, positions[i]);
    maxZ = Math.max(maxZ, positions[i]);
  }
  for (let i = 2; i < positions.length; i += 3) positions[i] -= (minZ + maxZ) / 2;

  const { Geometry, Attribute } = constructors;
  const geometry = new Geometry();
  geometry.setAttribute('position', new Attribute(new Float32Array(positions), 3));
  geometry.setAttribute('normal', new Attribute(new Float32Array(normals), 3));
  geometry.setAttribute('uv', new Attribute(new Float32Array(uvs), 2));
  for (const { start, count, materialIndex } of groups) geometry.addGroup(start, count, materialIndex);
  geometry.computeBoundingBox();
  geometry.computeBoundingSphere();
  return { geometry, materials };
}

// The Straps section assembles a steel bracelet from instanced links. Keep
// that choreography but build the band from WHOOP knit segments instead.
async function replaceBraceletLinks(project, whoopScene) {
  const straps = await waitFor(
    () => project.webgl.sectionsController.sections?.find(section => section.name === 'Straps'),
    'Straps section',
  ).catch(() => null);
  if (!straps?.linkMesh) return;
  // Plain BufferGeometry/BufferAttribute constructors from the page's particles.
  const particles = project.webgl.particlesScene.particles.geometry;
  const segment = buildBandSegment(whoopScene, { Geometry: particles.constructor, Attribute: particles.attributes.position.constructor });
  straps.centralMesh?.layers.set(HIDDEN_LAYER);
  if (!segment) {
    straps.linkMesh.layers.set(HIDDEN_LAYER);
    return;
  }
  straps.linkMesh.geometry = segment.geometry;
  straps.linkMesh.material = segment.materials;
  straps.linkMesh.frustumCulled = false;
}

function sync(watch) {
  const now = performance.now();
  const dt = Math.min(0.1, (now - (state.lastTime || now)) / 1000);
  state.lastTime = now;

  for (const { part, pivot, rest } of state.links) {
    const mesh = part.mesh;
    pivot.position.set(rest.x, rest.y, rest.z + mesh.position.z - part.initialPos.z);
    pivot.rotation.set(mesh.rotation.x, mesh.rotation.y, mesh.rotation.z);
    pivot.visible = visibleInWatch(mesh, watch);
  }
  const { pivot, source, rest } = state.band;
  pivot.position.copy(source.position).sub(rest);
  pivot.visible = visibleInWatch(source, watch);

  // Colour changes ease like the page's power3 material tweens.
  const ease = 1 - Math.exp(-dt * 4);
  for (const material of variantMaterials(state.materials)) {
    const target = state.targetColors[VARIANT_MATERIALS[material.name]];
    material.userData.whoopTarget ??= material.color.clone();
    material.color.lerp(material.userData.whoopTarget.set(target), ease);
  }

  // The renderer updated world matrices before calling onBeforeRender.
  state.anchor.updateMatrixWorld(true);
}

async function init() {
  const project = await loadProject();
  state.project = project;
  // Start the WHOOP download alongside the page's own assets.
  await waitFor(() => project.assetsManager?.loaders?.models, 'page model loader');
  const mobile = project.assetsManager.isMobile;
  const mainPromise = loadWhoop(project, mobile ? MODEL_URL.light : MODEL_URL.full);

  // theWatch and its part table exist once the page attaches its scene.
  await waitFor(() => project.webgl?.scene?.watchParts && project.webgl.scene.watch, 'page scene');
  const scene = project.webgl.scene;
  // Hide the watch straight away; WHOOP appears as soon as its GLB is ready.
  hideOriginalMeshes(scene.watch, keepSet(scene));
  scene.watchesGroup?.watchesInsideGroup?.children.forEach(wrapper => hideOriginalMeshes(wrapper, new Set()));

  const whoopScene = await mainPromise;
  // Read the band before attachWhoop re-parents its groups; meshes share
  // geometry and materials with the attached model.
  const bandSource = whoopScene.clone(true);
  attachWhoop(project, whoopScene);
  document.body.classList.add('whoop-model-ready');

  replaceBraceletLinks(project, bandSource);
  const lightScene = mobile
    ? bandSource
    : await loadWhoop(project, MODEL_URL.light).catch(error => console.error('WHOOP footer model failed:', error));
  if (lightScene) addFooterWhoops(scene, lightScene);
  else restoreLayers(scene.watchesGroup);
}

init().catch(error => {
  console.error('WHOOP scene integration failed:', error);
  // Fall back to the original watches rather than an empty stage.
  const scene = state.project?.webgl?.scene;
  state.anchor?.removeFromParent();
  restoreLayers(scene?.watch);
  restoreLayers(scene?.watchesGroup);
  document.body.classList.add('whoop-model-failed');
});
