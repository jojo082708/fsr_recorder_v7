# 外穿式布鞋 FSR 雙點足底力量量測平台（AFO v17 草案）

由 AFO v15 修改：
- 小腿件不改（背面放麵包板）。
- 腳底件維持 AFO 托盤外形，刪除舊 FSR 構造。
- 第一蹠骨頭與腳跟各裝一組鋼珠式 FSR 402 感測匣，走線經後跟杯背面接到小腿件。

| 路徑 | 內容 |
|---|---|
| `drawings/FSR_AFO_v17_Drawings.pdf` | 工程圖 12 張（A3），各張 PNG 也在同一資料夾 |
| `docs/設計說明.md` | 參數表（標示待確認）、零件尺寸表、BOM、組裝、列印建議 |
| `cad/afo_v17.py` | 模型：v15 網格 + 布林運算 + CadQuery 感測匣 |
| `cad/make_drawings.py` | 產生工程圖（約 1 分鐘） |
| `cad/data/v15/` | v15 原件（由 STEP 轉成 STL） |
| `cad/data/footprint_outline_mm.csv` | 腳印輪廓 |

```bash
pip install cadquery manifold3d trimesh embreex shapely scipy matplotlib pillow mapbox_earcut rtree
python3 cad/make_drawings.py drawings
python3 cad/afo_v17.py --export out      # 圖面確認後輸出 STL + STEP
```
