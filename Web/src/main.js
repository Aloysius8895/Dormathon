import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { loadWhoop, createVariant, conceptVariants, setExplosion } from './whoop-binding.js';
import './style.css';

const stage = document.querySelector('#model-stage');
const canvas = document.querySelector('#model-canvas');
const fallback = document.querySelector('#model-fallback');
const loaderOverlay = document.querySelector('#loader');
const loadProgress = document.querySelector('#load-progress');
const variantList = document.querySelector('#variant-list');
const partList = document.querySelector('#part-list');
const explodeProgress = document.querySelector('#explode-progress');
const explodeValue = document.querySelector('#explode-value');
const pageProgress = document.querySelector('#page-progress');
const hero = document.querySelector('.hero');
const assembly = document.querySelector('.assembly-section');
const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
const mobileModel = matchMedia('(max-width: 768px)').matches;

let renderer;
let scene;
let camera;
let display;
let models = [];
let selectedIndex = 0;
let activeScene = 'hero';
let explosion = 0;
let pointerDown = false;
let pointerX = 0;
let pointerY = 0;
let targetRotationX = -.13;
let targetRotationY = -.55;
let baseScale = 1;
let targetScale = 1;

function clamp(value, min, max) { return Math.max(min, Math.min(max, value)); }

function markLoaded() {
  loadProgress.textContent = '100%';
  loaderOverlay.classList.add('is-done');
  setTimeout(() => loaderOverlay.remove(), 850);
}

function makeVariants() {
  conceptVariants.forEach((variant, index) => {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'variant-button' + (index === 0 ? ' is-active' : '');
    button.style.setProperty('--swatch', variant.strap);
    button.setAttribute('aria-label', `Show ${variant.name} concept color`);
    button.setAttribute('aria-pressed', String(index === 0));
    button.innerHTML = `<span class="variant-swatch"></span><span>${variant.name.toUpperCase()}</span>`;
    button.addEventListener('click', () => selectVariant(index));
    variantList.append(button);
  });
}

function selectVariant(index) {
  selectedIndex = index;
  models.forEach((model, current) => {
    model.visible = current === index;
    if (current === index) setExplosion(model, explosion);
  });
  [...variantList.children].forEach((button, current) => {
    button.classList.toggle('is-active', current === index);
    button.setAttribute('aria-pressed', String(current === index));
  });
}

async function makeParts() {
  try {
    const response = await fetch('/whoop/content/parts.json');
    if (!response.ok) throw new Error(`Parts: ${response.status}`);
    const { parts } = await response.json();
    parts.forEach((part, index) => {
      const card = document.createElement('article');
      card.className = 'part-card';
      card.innerHTML = `<img src="/whoop/${part.image}" alt="Illustrative ${part.title.toLowerCase()} component" loading="lazy"><div><span>${String(index + 1).padStart(2, '0')} / 06</span><h3>${part.title}</h3><p>${part.copy}</p></div>`;
      partList.append(card);
    });
  } catch (error) {
    partList.textContent = 'Component gallery unavailable.';
    console.error(error);
  }
}

function resize() {
  if (!renderer || !camera) return;
  const width = Math.max(1, stage.clientWidth);
  const height = Math.max(1, stage.clientHeight);
  renderer.setSize(width, height, false);
  camera.aspect = width / height;
  camera.position.z = camera.aspect < .9 ? 8.5 : 7.5;
  camera.updateProjectionMatrix();
}

function updateScroll() {
  const documentHeight = Math.max(1, document.documentElement.scrollHeight - innerHeight);
  pageProgress.style.height = `${(scrollY / documentHeight) * 100}%`;
  const heroBox = hero.getBoundingClientRect();
  const assemblyBox = assembly.getBoundingClientRect();
  const narrow = innerWidth <= 900;
  const assemblyVisible = assemblyBox.top < (narrow ? -innerHeight * .4 : 0) && assemblyBox.bottom > innerHeight * .12;
  const heroVisible = heroBox.top < innerHeight && heroBox.bottom > 0;
  const nextScene = assemblyVisible ? 'assembly' : heroVisible ? 'hero' : 'none';
  if (nextScene !== activeScene) {
    targetRotationY = nextScene === 'assembly' ? 1.18 : -.55;
    targetRotationX = nextScene === 'assembly' ? -.08 : -.13;
  }
  activeScene = nextScene;
  targetScale = baseScale * (activeScene === 'assembly' ? (narrow ? .58 : .72) : 1);
  stage.classList.toggle('is-visible', activeScene !== 'none');
  stage.classList.toggle('is-assembly', activeScene === 'assembly');
  explosion = activeScene === 'assembly'
    ? clamp((-assemblyBox.top - (narrow ? innerHeight * .4 : 0)) / (innerHeight * .7), 0, 1)
    : 0;
  if (models[selectedIndex]) setExplosion(models[selectedIndex], explosion);
  explodeProgress.style.width = `${Math.round(explosion * 100)}%`;
  explodeValue.textContent = `${String(Math.round(explosion * 100)).padStart(2, '0')}%`;
  requestAnimationFrame(resize);
}

function animate() {
  requestAnimationFrame(animate);
  if (!renderer || !display) return;
  if (!pointerDown && !reducedMotion && activeScene === 'hero') targetRotationY += .0013;
  display.rotation.x += (targetRotationX - display.rotation.x) * .05;
  display.rotation.y += (targetRotationY - display.rotation.y) * .05;
  display.scale.setScalar(display.scale.x + (targetScale - display.scale.x) * .08);
  if (activeScene !== 'none') renderer.render(scene, camera);
}

async function initModel() {
  try {
    renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true, powerPreference: 'high-performance' });
    renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 2));
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.8;
    scene = new THREE.Scene();
    camera = new THREE.PerspectiveCamera(36, 1, .01, 100);
    camera.position.set(0, 0, 7.5);
    scene.add(new THREE.HemisphereLight(0xffffff, 0x7f8586, 3.5));
    const key = new THREE.DirectionalLight(0xffffff, 4.8); key.position.set(3, 4, 5); scene.add(key);
    const rim = new THREE.DirectionalLight(0xc2d0ce, 3); rim.position.set(-4, -2, -3); scene.add(rim);
    display = new THREE.Group();
    scene.add(display);

    const manager = new THREE.LoadingManager();
    manager.onProgress = (_url, loaded, total) => { loadProgress.textContent = `${Math.min(98, Math.round(loaded / total * 100))}%`; };
    const gltf = await loadWhoop(new GLTFLoader(manager), mobileModel ? '/whoop/model/whoop-mobile.glb' : '/whoop/model/whoop-web.glb');
    const bounds = new THREE.Box3().setFromObject(gltf.scene);
    const size = bounds.getSize(new THREE.Vector3());
    const center = bounds.getCenter(new THREE.Vector3());
    baseScale = 2.75 / Math.max(size.x, size.y, size.z);
    targetScale = baseScale;
    models = conceptVariants.map(variant => {
      const model = createVariant(gltf.scene, variant);
      model.position.sub(center);
      model.visible = false;
      display.add(model);
      return model;
    });
    display.scale.setScalar(baseScale);
    display.rotation.set(targetRotationX, targetRotationY, 0);
    selectVariant(selectedIndex);
    resize();
    updateScroll();
    markLoaded();
  } catch (error) {
    console.error('WHOOP model could not be rendered:', error);
    canvas.hidden = true;
    fallback.hidden = false;
    document.querySelector('.model-hint').textContent = 'WHOOP 5.0 CONCEPT';
    markLoaded();
  }
}

stage.addEventListener('pointerdown', event => {
  pointerDown = true; pointerX = event.clientX; pointerY = event.clientY;
  stage.setPointerCapture(event.pointerId);
});
stage.addEventListener('pointermove', event => {
  if (!pointerDown) return;
  targetRotationY += (event.clientX - pointerX) * .008;
  targetRotationX = clamp(targetRotationX + (event.clientY - pointerY) * .006, -1.1, 1.1);
  pointerX = event.clientX; pointerY = event.clientY;
});
stage.addEventListener('pointerup', () => { pointerDown = false; });
stage.addEventListener('pointercancel', () => { pointerDown = false; });
addEventListener('resize', () => { resize(); updateScroll(); });
addEventListener('scroll', updateScroll, { passive: true });
makeVariants();
makeParts();
updateScroll();
animate();
initModel();
