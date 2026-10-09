# WHOOP 5.0 素材包

先打开 `preview/WHOOP_Assets_Preview.html`。文件离线可用，支持旋转、缩放、四套换色、六组拆解和扣具展示。
页面使用轻量 WebGL 着色，正式模型的 PBR 贴图请在 Three.js / Blender 中查看。

## 文件导航

- `brief.md`：默认产品、配色、页面语言与制作范围。
- `model/whoop-web.glb`：桌面模型，独立零件、织物纹理、两个动画 clip。
- `model/whoop-mobile.glb`：轻量模型，减少几何织纹。
- `model/whoop-source.gltf` + `.bin`：可编辑的未压缩源模型。
- `model/whoop-source.npz`：未压缩原始网格数组。
- `model/textures/`：底色、法线、金属度/粗糙度、AO 贴图。
- `variants/`：Graphite、Dune、Sage、Cobalt 配色配置及渲染图。
- `renders/`：五张段落展示图、六张零件特写。
- `content/`：中英文文案、零件列表、分享图、favicon、官方资料链接。
- `integration/`：Three.js 模型绑定、换色、拆解代码与接入说明。
- `source/`：重建程序、Blender 转换脚本、预览生成程序。
- `references/`：用户原始参考图。
- `rights.md`：素材来源记录。
- `validation.json`：模型结构与资源验证结果。

## 使用说明

解压后保持目录关系。用 Chrome / Edge 打开离线预览；浏览器须启用 WebGL。
正式接入时复制整个 whoop-assets 文件夹到项目的静态资源目录，按 integration/README.md 使用。
仅加载一个模型，再克隆实例和材质，不需要加载四个独立 GLB。

此包是 WHOOP 5.0 风格的概念重建。内部布局和颜色为示意，非官方 CAD 或商品 SKU。
当前未提供 .blend；安装 Blender 后运行 `blender --background --python source/create_blend.py` 可以生成。

各配色包含 front、back-sensor、side 和 worn-concept 图。worn-concept 使用简化手腕几何示意，并非实物佩戴照片。
