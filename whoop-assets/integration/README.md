# 将手表页面替换成 WHOOP

此包包含素材、配置和接入模块；并未修改缺失的 template2。

## 1. 加载一次，创建四套展示

在已有 Three.js 项目中使用 GLTFLoader 与 `whoop-binding.js`：

```js
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { loadWhoop, createVariant, conceptVariants, setExplosion, setClaspOpen } from './whoop-binding.js';

const loader = new GLTFLoader();
const gltf = await loadWhoop(loader, '/whoop-assets/model/whoop-web.glb');
const products = conceptVariants.map(v => createVariant(gltf.scene, v));
products.forEach((root, i) => {
  root.position.x = (i - 1.5) * 0.11;
  scene.add(root);
});
// selectedIndex is your color selector's index, 0..3.
setExplosion(products[selectedIndex], scrollProgress);
setClaspOpen(products[selectedIndex], claspProgress);
```

材质必须对每个展示实例分别 clone；几何与贴图可以共享。
颜色值是 sRGB HEX。Three.js 的 Color.set() 负责转换；不要先手动做 gamma 转换再传入。

## 2. 零件绑定与动画

固定组名：Strap、Clasp、Housing、Haptics、Mainboard、Battery、Sensors、Backplate。
各组的 glTF extras.explode_delta 提供拆解位移，单位米。
动画 clip：WHOOP_Explode 与 WHOOP_ClaspOpen，时长 2 秒。
拆解排列方向为 Z；推荐视角从 +X 一侧观察，使六组横向展开。
参考图模式默认在拆解超过 10% 后隐藏 Strap / Clasp，单独展示六组内部零件。

可使用 AnimationMixer，或调用 setExplosion()/setClaspOpen()。同一组的同一 transform 请选一条控制路径。
若使用 clips，需自行绑定滚动时间，并按展示要求控制腕带与扣具 visibility。
扣具开合 clip 是概念展示变换，不是真实扣具运动学。

## 3. 替换原站内容

| 原站内容概念 | WHOOP 替代内容 | 对应资源 |
| --- | --- | --- |
| 表盘、指针 | 无屏幕传感器外观 | Housing / 01-hero.png |
| 陀飞轮、自动机芯 | 传感器主板与电池 | Mainboard / Battery |
| 手表表带 | 织物腕带 | Strap / 04-woven-band.png |
| 表冠 | 扣具与佩戴结构 | Clasp |
| 水晶、表圈 | 外壳与皮肤侧底盖 | Housing / Backplate |
| 机械拆解动画 | 六组概念拆解 | WHOOP_Explode |

此表是概念映射，不是旧站真实节点名。必须在恢复的 template2 中检查旧脚本的对象引用并逐一替换。

五个图片位置见 page-config.json；文案见 content/copy.md 与 copy.json。
充电介绍不等于自动机械上链；不要复用旧动画表达 WHOOP 的充电。

## 4. 材质与轻量版本

Strap_Fabric 可换色，已嵌入四张织物 PBR 贴图，材质为非金属。
Strap_Fibers 控制几何编织纹理的颜色。Clasp_Metal 控制扣具颜色。
其他材质包括 Housing_Matte、Sensor_Glass、Sensor_LED、PCB、Chip、Gold_Contacts、Battery_Foil、Haptics_Metal。
手机版本移除几何编织起伏，保留织物 PBR 贴图、分组和两个动画 clip。
请按实际设备实测性能；四个高细节模型同时展示会增加绘制负担。

## 5. 源文件

whoop-source.gltf + whoop-source.bin 是未压缩的可编辑 glTF 源模型。
whoop-source.npz + source-manifest.json 提供原始顶点、法线与三角面数组。
source/build_assets.py 可重建 GLB、材质图与渲染图，需要 Python、NumPy、Pillow。
source/create_blend.py 可在安装 Blender 的机器中生成 whoop-source.blend。
本包没有伪造 .blend 文件。

## 6. 仍需要由原项目决定的内容

旧页面滚动触发点、灯光、镜头路径、布局、动画时序及交互入口。
真实商品的 SKU、价格、购买链接与商业素材许可。
真实佩戴摄影没有生成；提供的 front/back/side 都是概念 3D 渲染。

拆解过程中，Sensors 与 Backplate 额外绕 Y 轴旋转 180°，让光学窗口朝向展示镜头；该变换是演示处理，不是真实拆卸动作。
