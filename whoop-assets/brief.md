# WHOOP 网站替换素材包

- 产品：WHOOP 5.0（默认选择，可后续修改）。
- 腕带：SuperKnit 风格的织物腕带；本模型为视觉重建。
- 页面：英文主文案，附中文对照。
- 款式：Graphite、Dune、Sage、Cobalt，四套概念配色，非官方 SKU。
- 用途：本地网页原型与演示；不标注为 WHOOP 官方页面。
- 展示方式：一个 GLB 共享几何，复制四个展示实例，各自克隆材质后换色。
- 滚动顺序：外观 → 佩戴方式 → 光学感测 → 织物结构 → 六组拆解 → 充电介绍。
- 单位：米。传感器外部包络以 34.7 × 24 × 10.6 mm 为目标；腕带及内部零件尺寸为近似值。
- 默认朝向：腕带环在 XY 平面，传感器位于 +X；传感器长轴为 Y，宽轴为 Z。
- 独立展示组：Strap、Clasp、Housing、Haptics、Mainboard、Battery、Sensors、Backplate。
- 内部零件按用户给的拆解图作视觉示意，不表示真实 WHOOP 5.0 PCB 或精确装配关系。
- 原站 template2 及其抓取文件不在本次提供的文件中，本包提供素材与接入代码，不声称已完成原站替换。

## 本包的源文件

提供未压缩的 `model/whoop-source.npz` 网格数据、`source-manifest.json` 和可重建代码。
当前环境未安装 Blender，因此未生成 .blend。`source/create_blend.py` 可在 Blender 中导入 GLB 并保存 .blend，包含材质、分组和动画。

## 产品资料

外部规格与功能依据 `content/sources.md` 中列出的官方页面，核对日期 2026-10-09。
模型外观、颜色、图片和内部示意是本次制作的概念素材。
