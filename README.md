# 外穿式布鞋 FSR 雙點足底力量量測平台（AFO v17 草案）

由 AFO v15 修改。兩個版本：

| 版本 | 依據 | 腳底件 | 列印 |
|---|---|---|---|
| 穿鞋版 `shoe` | 鞋底 310 × 110 | 346 × 134 × 76 | 兩件（x = 120 搭接，6 × M4） |
| 赤腳版 `barefoot` | 腳掌 254 × 100 | 285 × 122 × 76 | 一件（無鞋頭擋塊） |

兩版共用的部分：
- 小腿件不改，背面放麵包板。
- 後跟杯介面不變。
- 兩組鋼珠式 FSR 402 感測匣：Ø42 凸環高出底板 3 mm，位置固定。
- 走線槽加蓋板，從後跟杯背面出線。

| 路徑 | 內容 |
|---|---|
| `drawings/shoe/`、`drawings/barefoot/` | 各版工程圖 PNG 與 PDF |
| `drawings/16_兩版本比較_赤腳版_vs_穿鞋版.png` | 兩版本比較圖 |
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
