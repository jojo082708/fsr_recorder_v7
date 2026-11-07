# 外穿式布鞋 FSR 雙點足底力量量測平台（AFO v17 草案）

由 AFO v15 修改，**模組化可拆卸**：共用後段 + 可換前段（x = 120 搭接，6 × M4 螺絲）。

| 模組 | 依據 | 前段 | 整體 | 另附 |
|---|---|---|---|---|
| 共用後段 F1A | — | 139 × 112 × 76（後段） | — | 感測匣 ×2、走線蓋板 |
| 穿鞋前段 `shoe` | 鞋底 310 × 110 | 240 × 134 × 39 | 349 × 134 | v15 造型鞋頭擋塊 |
| 赤腳前段 `barefoot` | 腳掌 254 × 100 | 190 × 122 × 39 | 299 × 122 | 客製鞋頭擋塊、H1 腳跟墊塊 12 mm |

赤腳時插入腳跟墊塊，讓腳跟位置與穿鞋相同 → 兩組感測器位置不變（S1 197.3, −25；S2 45.3, +12）。
任意尺寸：`python3 cad/export_kit.py out/kit shoe:300x105 barefoot:240x95`。

兩版共用的部分：
- 小腿件不改，背面放麵包板。
- 後跟杯介面不變。
- 兩組鋼珠式 FSR 402 感測匣：Ø42 凸環高出底板 3 mm，位置固定。
- 走線槽加蓋板，從後跟杯背面出線。

| 路徑 | 內容 |
|---|---|
| `drawings/shoe/`、`drawings/barefoot/` | 各版工程圖 PNG 與 PDF |
| `drawings/16_兩版本比較_赤腳版_vs_穿鞋版.png` | 兩版本比較圖 |
| `drawings/17_模組化套件_共用後段_可換前段.png` | 模組化套件圖 |
| `cad/export_kit.py` | 輸出模組化套件（共用後段 + 各尺寸前段） |
| `drawings/textcad/` | text-to-cad（cadgen）前後對照的快照圖 |
| `docs/設計說明.md` | 參數表、BOM、組裝、列印建議 |
| `cad/afo_v17.py` | 模型；版本用 `AFO_VARIANT=shoe` 或 `AFO_VARIANT=barefoot` 切換 |
| `textcad/` | cadgen 模型腳本 |
| `viewer/index.html` | 3D 檢視頁原始碼 |

```bash
pip install cadquery manifold3d trimesh embreex shapely scipy matplotlib pillow mapbox_earcut rtree
AFO_VARIANT=barefoot python3 cad/make_drawings.py drawings/barefoot
AFO_VARIANT=barefoot python3 cad/afo_v17.py --export out/barefoot     # STL / 3MF / STEP
python3 cad/make_variants_sheet.py drawings                            # 兩版本比較圖
```
