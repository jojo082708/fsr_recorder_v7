# 外穿式布鞋 FSR 雙點足底力量量測平台（AFO v16 草案）

由 AFO v15 修改而來：
- 腳底板外形依使用者腳印客製。
- 第一蹠骨頭與腳跟兩處各裝一組鋼珠式 FSR 402 感測模組。
- 後跟外側加裝 ESP32 電控盒。

| 路徑 | 內容 |
|---|---|
| `drawings/FSR_Platform_Drawings.pdf` | 工程圖 12 張（A3），各張 PNG 也在同一資料夾 |
| `docs/設計說明.md` | 尺寸參數表（標示待確認）、零件尺寸表、BOM、組裝流程、校正流程、3D 列印建議 |
| `cad/fsr_platform.py` | CadQuery 參數化模型，所有尺寸都在檔案開頭的 `P` |
| `cad/make_drawings.py` | 由模型產生工程圖 |
| `cad/data/footprint_outline_mm.csv` | 由腳印照片數位化的足型輪廓（mm） |

```bash
pip install cadquery shapely trimesh scipy matplotlib pillow
python3 cad/make_drawings.py drawings          # 重新產生工程圖（約 10 分鐘）
python3 cad/fsr_platform.py --export out       # 確認圖面後：輸出 STL + STEP
```
