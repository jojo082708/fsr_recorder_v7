# ALICE 風格下肢外骨骼 — AK70-10（髖）+ AK60-6（膝），3D 列印連桿

| 檔案 | 內容 |
|---|---|
| `exo_ak.py` | 參數化模型（CadQuery）。馬達尺寸、段長、插槽、孔位都在檔頭 `MOTORS` / `P` |
| `make_sheets.py` | 把算圖組成 A3 工程圖（`drawings/exo/`） |
| `render/` | three.js 算圖頁 + Playwright 截圖腳本 |
| `stl/` | 每個列印件 STL（單腳、左腳；右腳在切片軟體鏡射） |
| `exo_ak_left.step` / `.glb` | 整腳組合 |

- 馬達外形：AK70-10 Ø89 × 50.25、AK60-6 V1.1 Ø79 × 39.5（CubeMars 官網）。
- **鎖孔 PCD / 數量是示意值**，請量實物或下載官方 STEP 後改 `MOTORS`，再重跑。
- 段長 390–450（每 15）：`P["THIGH"]`、`P["SHANK"]`。

```bash
pip install cadquery trimesh shapely matplotlib pillow
python3 exo/exo_ak.py --export out/exo                 # STL / STEP / GLB
python3 exo/exo_ak.py --export out/exo_pose --hip 25 --knee 35
```
