import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { loadWhoop, createVariant, conceptVariants, setExplosion } from './whoop-binding.js';

// The original page and its scroll choreography remain untouched. This canvas
// only replaces the visible product render inside the existing canvas wrapper.
const wrapper = document.querySelector('#canvas-wrapper');
const canvas = document.createElement('canvas');
canvas.className = 'whoop-overlay-canvas';
canvas.setAttribute('aria-label', 'WHOOP 3D model');
wrapper.append(canvas);

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(35, 1, 0.01, 100);
camera.position.set(0, 0, 7.5);
scene.add(new THREE.HemisphereLight(0xffffff, 0x777b80, 3.5));
const key = new THREE.DirectionalLight(0xffffff, 4.5);
key.position.set(3, 4, 5);
scene.add(key);
const rim = new THREE.DirectionalLight(0xc5d4dc, 2.5);
rim.position.set(-4, -2, -3);
scene.add(rim);

const display = new THREE.Group();
scene.add(display);
const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.7;

let variants = [];
let selected = 0;
let baseScale = 1;
let targetRotation = -0.65;
let targetScale = 1;
let targetX = 0;
let targetY = 0;
let visible = true;
let explosion = 0;

function resize() {
  const width = Math.max(1, window.innerWidth);
  const height = Math.max(1, window.innerHeight);
  renderer.setSize(width, height, false);
  camera.aspect = width / height;
  camera.position.z = width < 700 ? 9.2 : 7.5;
  camera.updateProjectionMatrix();
}

function select(index) {
  selected = index;
  canvas.dataset.variant = conceptVariants[index].id;
  variants.forEach((model, i) => { model.visible = i === index; });
  setExplosion(variants[index], explosion, { hideBand: false });
}

function sectionAtViewportCenter() {
  const sections = [...document.querySelectorAll('[data-webgl]')];
  return sections.find(element => {
    const rect = element.getBoundingClientRect();
    return rect.top <= window.innerHeight * 0.5 && rect.bottom > window.innerHeight * 0.5;
  }) || sections.find(element => {
    const rect = element.getBoundingClientRect();
    return rect.top < window.innerHeight && rect.bottom > 0;
  });
}

function updateFromPage() {
  const section = sectionAtViewportCenter();
  const name = section?.getAttribute('data-webgl') || 'Intro';
  const rect = section?.getBoundingClientRect();
  const progress = rect ? THREE.MathUtils.clamp((window.innerHeight * 0.5 - rect.top) / Math.max(rect.height, 1), 0, 1) : 0;
  const narrow = window.innerWidth < 700;

  visible = !['Images', 'Parts', 'Footer'].includes(name);
  explosion = name === 'Disassembly' ? THREE.MathUtils.smoothstep(progress, 0.1, 0.8) * 0.3 : 0;
  if (variants[selected]) setExplosion(variants[selected], explosion, { hideBand: false });
  targetScale = baseScale * (name === 'Disassembly' ? 0.55 : name === 'Colors' ? 0.75 : 1);
  targetRotation = name === 'Disassembly' ? 0.7 : name === 'Straps' ? 0.1 : -0.65;
  targetX = name === 'Presentation' && !narrow ? window.innerWidth * 0.16 : 0;
  targetY = name === 'Disassembly' ? -window.innerHeight * 0.04 : 0;
  canvas.style.opacity = visible ? '1' : '0';
}

document.addEventListener('click', event => {
  const config = event.target.closest('[data-config]')?.getAttribute('data-config');
  const index = ['first', 'second', 'third', 'fourth'].indexOf(config);
  if (index >= 0 && variants.length) select(index);
}, true);
window.addEventListener('resize', () => { resize(); updateFromPage(); });
window.addEventListener('scroll', updateFromPage, { passive: true });

function animate() {
  requestAnimationFrame(animate);
  if (!variants.length) return;
  display.rotation.y += (targetRotation - display.rotation.y) * 0.06;
  display.rotation.x += (-0.16 - display.rotation.x) * 0.06;
  const scale = display.scale.x + (targetScale - display.scale.x) * 0.08;
  display.scale.setScalar(scale);
  display.position.x += (targetX / window.innerWidth * 4 - display.position.x) * 0.06;
  display.position.y += (-targetY / window.innerHeight * 4 - display.position.y) * 0.06;
  renderer.render(scene, camera);
}

async function init() {
  try {
    const mobile = matchMedia('(max-width: 700px)').matches;
    const modelUrl = mobile ? '/whoop/model/whoop-mobile.glb' : '/whoop/model/whoop-web.glb';
    const gltf = await loadWhoop(new GLTFLoader(), modelUrl);
    const box = new THREE.Box3().setFromObject(gltf.scene);
    const size = box.getSize(new THREE.Vector3());
    const center = box.getCenter(new THREE.Vector3());
    baseScale = (mobile ? 1.35 : 2.8) / Math.max(size.x, size.y, size.z);
    variants = conceptVariants.map(variant => {
      const model = createVariant(gltf.scene, variant);
      model.position.sub(center);
      display.add(model);
      return model;
    });
    display.scale.setScalar(baseScale);
    targetScale = baseScale;
    display.rotation.set(-0.16, targetRotation, 0);
    resize();
    select(selected);
    updateFromPage();
    renderer.render(scene, camera);
    document.body.classList.add('whoop-model-ready');
    animate();
  } catch (error) {
    console.error('WHOOP model load failed:', error);
    canvas.remove();
    renderer.dispose();
  }
}

init();
