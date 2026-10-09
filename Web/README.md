# FS 60P 页面中的 WHOOP 模型

此目录保留原始 FS 60P 页面结构、文案、样式和滚动效果。页面中可见的 3D 产品模型由 `../whoop-assets` 提供的 WHOOP GLB 渲染。

## 启动

```powershell
python serve.py
```

打开 <http://127.0.0.1:8081/>。也可以运行 `python serve.py --port 8082`。`site/` 已包含构建好的文件，浏览器需支持 WebGL。

## 模型接入

- 原站 HTML 和编译资源保存在 `site/index.html` 与 `site/assets/`，未作修改。
- `src/whoop-scene.js` 使用原站自带的 Three.js（r162）GLTFLoader 加载 WHOOP，把它挂到原站 WebGL 场景的 `theWatch` 节点下。原站的 GSAP 时间线、相机、后期处理、悬停与点击、长按全部拆开都照常运行：
  - 开场旋转、Presentation、Colors 等段落直接驱动 `theWatch`，WHOOP 作为子节点随之运动。
  - 拆解时，WHOOP 的六组零件逐帧复制旧表对应层的位移、旋转和显隐：`xploded-9 → Backplate`、`xploded-10 → Sensors`、`xploded-28 → Battery`、`xploded-29 → Mainboard`、`xploded-42 → Haptics`、`xploded-45 → Housing`。Strap 与 Clasp 跟随 `empty-strap`。
  - 旧表网格仍留在场景里，供原站的射线检测框和标签定位使用，只是放到相机不渲染的图层。
  - Straps 段沿用原站的实例化链节动画，链节换成从 WHOOP 腕带截取的织物段。
  - Footer 段的四个配色款换成轻量版 WHOOP（`whoop-mobile.glb`），配色为 Graphite、Dune、Sage、Cobalt。原站切换配色（`first`…`fourth`）时，主模型腕带颜色同步渐变。
- 桌面端主模型加载 `site/whoop/model/whoop-web.glb`，移动端加载 `whoop-mobile.glb`。
- 原站仍需 `site/assets/watch-DXFPNOEl.glb` 初始化动画和交互。WHOOP 加载失败时，页面会恢复显示原手表。
- 页面图片和文案保持原站内容，包括拆解段的零件标签（Dial、Tourbillon 等）。
- 上一版在原画布上方叠加独立画布的实现已移到 `legacy/overlay/`，不再使用。

修改接入代码后，运行 `npm install` 和 `npm run build`。运行 `python tools/verify_scene.py` 检查桌面和移动端：逐段滚动截图，确认旧表不可见、WHOOP 跟随原时间线，并测试拆解段的点击放大和长按拆开。截图写入 `verification/scene/`。
