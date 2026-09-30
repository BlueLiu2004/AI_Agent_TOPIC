# OnboardBot 程式架構速讀影片

給懂基本 Python、尚不熟 LangGraph、Corrective RAG 與 MCP 的觀眾。成片為 **3 分 12 秒、1920×1080、30 fps**，含繁體中文字幕與本機繁中語音。所有重要概念均有字幕與畫面說明，可以靜音觀看。

## 成品與文件

- [播放 MP4](out/onboardbot-tutorial.mp4)
- [分鏡與事實查核](storyboard.md)
- [旁白逐字稿](narration.md)
- [SRT 字幕](captions.srt)
- [成品 QA 紀錄](qa-report.md)
- [原始碼 SHA256 清單](source-manifest.json)

影片以三條故事線組織：

1. **選資訊來源**：Router 的 internal / external / hybrid；State、Node、Edge、Conditional Edge 如何合作。
2. **追蹤 Node.js 版本**：it-01 指定 22.11.0 → documents → relevant → internal_context → 擷取主版本 22 → web_query → Tavily MCP → 分開內部規範與公開來源。
3. **資料不相關時怎麼辦**：telecommuting → 改寫成「遠端工作政策」→ 重試；說明上限與 fallback，並區分測試通過和線上答案品質。

## 時間軸

| 時間 | 內容 |
|---|---|
| 00:00–00:12 | 一題需要內部與公開資訊 |
| 00:12–00:34 | 三路 Router |
| 00:34–00:54 | State 與真正的條件連線程式碼 |
| 00:54–01:40 | Node.js hybrid 完整追蹤 |
| 01:40–02:12 | Corrective RAG 改寫回圈 |
| 02:12–02:36 | MCP、官方網域與 URL 核對 |
| 02:36–02:58 | 14 項測試與歷史實驗 |
| 02:58–03:12 | 真正的完整圖與三個重點 |

## 本機編輯與重新輸出

先進入本目錄。此處有獨立的 Node dependencies，不需要變動 Python 應用。

```powershell
npm.cmd ci
npm.cmd run typecheck
npm.cmd run studio
```

Studio 使用本目錄的空白 `render.env`。影片只使用已打包的 JSON、字型和 WAV，不匯入 Python 應用，也不載入其 `.env`。

完整輸出：

```powershell
npm.cmd run render
```

程式化 renderer 會使用 Windows 標準位置的 Chrome；其他安裝位置可指定：

```powershell
$env:REMOTION_BROWSER = 'C:/path/to/chrome.exe'
npm.cmd run render
```

如果沒有指定 browser，而且找不到預設 Chrome，Remotion 可能下載 Chrome Headless Shell。重現原成片使用 Node.js 26.7.0、Remotion 4.0.529 與本機 Chrome。安裝相依套件需要網路；實際影片內容不依賴遠端模型、搜尋或字型。

### 修改畫面

| 檔案 | 用途 |
|---|---|
| `src/index.ts` | Composition：1920×1080、30 fps、5760 frames |
| `src/Video.tsx` | 場景時間、字型、字幕層、音軌與總版面 |
| `src/scenes.tsx` | 八個場景及 State 變化 |
| `src/components.tsx` | ArchitectureGraph、StateInspector、CodePanel、DataToken 等 |
| `src/data/scenes.json` | 場景起訖、標題與章節 |
| `src/data/cues.json` | 字幕與旁白的唯一文字來源 |
| `src/data/source.json` | 真實程式碼節錄、圖結構、政策與留存實驗摘要 |
| `public/audio/voiceover.wav` | 已產生的完整旁白，重新渲染不必重建 TTS |
| `public/fonts/` | 隨附 Noto Sans TC、JetBrains Mono 與 OFL 授權 |

動畫依 frame 計算，沒有隨機值或即時 API 回應。程式碼摘錄保留檔名、行號，顯示時只去除共同縮排。

### 修改字幕與旁白

先編輯 `src/data/cues.json` 的 `text`；`speech` 可為英文識別名稱提供較自然的中文讀法。兩者意思需一致。

```powershell
npm.cmd run captions
npm.cmd run audio
node scripts/mix-audio.mjs
npm.cmd run render
```

語音使用 Windows `System.Speech` 的 **Microsoft Hanhan Desktop / zh-TW**，未使用任何線上 TTS。重建音訊需要該本機 voice，以及 PATH 上的 FFmpeg/FFprobe。33 段語音依 cue 起始時間混音；本片最大速度調整約 1.21 倍。若沒有相同 voice，保留隨附 WAV 即可重新 render。

變動整體時間時，也要更新 Composition、音軌長度與驗證腳本中的 192 秒設定。

## 驗證

```powershell
npm.cmd run typecheck
..\.venv\Scripts\python.exe scripts/verify-source.py
..\.venv\Scripts\python.exe -B scripts/run-offline-tests.py
npm.cmd run qa:stills
node scripts/qa-video.mjs
```

- `verify-source.py`：核對 21 個來源 SHA256、5 段摘錄、8 節點／14 連線與字幕時間。
- `run-offline-tests.py`：執行既有 14 個 fake-service 測試；阻止 dotenv 載入與對外 socket 連線。Windows asyncio 必需的 loopback 保留。未修改應用與測試檔。
- `render-stills.mjs`：輸出 Remotion 靜態預覽，可在命令後指定秒數。
- `qa-video.mjs`：對實際 MP4 做 FFprobe、完整解碼、黑畫面偵測、音量檢查，並擷取 10 個成品畫面。仍應人工檢視圖片是否可讀及語意正確。

如要更新來源快照，可執行 `scripts/snapshot.py`；它會覆寫來源摘要與 SHA256 清單。只有在重新閱讀原始碼、檢查分鏡與視覺內容後才這樣做，以免舊影片搭配新證據。

## 證據與限制

- TechCore 與政策皆為虛構示範。當前政策是 **22.11.0**；程式只提取主版本 **22** 建立搜尋字串。
- retrieve 寫 documents；grade relevant 才寫 internal_context。文件組的相關性評分並非逐項事實驗證。
- telecommuting 回圈標示為 **可控測試示範**。09/25 線上實驗實際曾誤分 hybrid。
- 09/24 六題完成三題，其餘模型 503；09/25 六題皆完成。這是留存紀錄，不能推論目前服務永久正常。
- 09/25 Node.js 搜尋曾包含 v12.22.1 舊頁，影片保留這個反例。官方網域及 URL 一致性不能證明搜尋頁相關或最新。
- 正常 JSON 搜尋結果會再次檢查網域；非 JSON fallback 沒有相同的二次網域過濾。
- 原應用有自己的依賴；影片專案只讀原始碼與留存紀錄。既有 `.env.example` 刪除及未追蹤壓縮檔並非本次變更。

本次新增內容均在 `tutorial-video/`。輸出 MP4、暫存、node_modules、原始 TTS 分段及 QA 圖片不加入 Git，實際檔案保留在本機；如需分享成品，請一併傳送 `out/onboardbot-tutorial.mp4`。
