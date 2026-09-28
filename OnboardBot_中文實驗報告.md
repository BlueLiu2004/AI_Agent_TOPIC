# OnboardBot 中文實驗報告

**實驗主題：** LangGraph Corrective RAG 與 Tavily MCP 整合驗證

**實驗日期：** 2026 年 9 月 24 日（臺灣時間）

**實驗對象：** TechCore 新人助理教學專案（TechCore 與政策內容均為虛構）

**報告範圍：** 程式結構、可控測試、實際服務問答與限制

## 摘要

本實驗將既有 Corrective RAG 範例擴充為三路問答流程：公司內部問題使用 Chroma 檢索，公開問題使用 Tavily 遠端 MCP，混合問題先取得內部依據，再用它建立外部搜尋字串。專案以 LangGraph 的 State、Node 與 Conditional Edge 表達路由、相關性評分、查詢改寫及重試上限。資料集為 50 筆繁體中文虛構政策。

驗證結果分為兩層。使用替身模型、向量庫與搜尋工具的 14 項測試全部通過，證明主要圖分支及錯誤處理符合程式預期。2026 年 9 月 24 日 19:59 至 20:02 的真實服務實測中，六題有三題完成；另外三題在 NVIDIA 模型呼叫時收到 HTTP 503，重跑一次後仍失敗。完成的加班題成功走完混合路徑，但生成文字末段截斷。因此目前能證實架構及部分真實問答可運作，不能宣稱六題線上問答全部通過。

## 一 實驗目標與系統設計

實驗檢查四件事：（1）內部、外部與混合問題能否進入正確路徑；（2）內部檢索不相關時能否改寫查詢，並在上限後停止；（3）混合問題能否把內部檢索結果傳入外部搜尋；（4）回答能否保留內外來源及服務失敗訊息。

原版流程固定由檢索開始，經文件相關性評分後，選擇回答、改寫重試或 fallback。本版在入口加入 Router，並接上 Tavily MCP。圖的主要資料流如下：

`START → router → internal: retrieve → grade → generate`

`START → router → external: build_web_query → tavily_search → generate`

`START → router → hybrid: retrieve → grade → build_web_query → tavily_search → generate`

若評分為不相關且尚未達重試上限，流程走 `rewrite_query → retrieve`；上限為兩次改寫，之後走 `fallback_generate`。`original_question` 保留原問句，`question` 可改寫；`internal_context`、`web_query`、`web_urls` 與 `trace` 分別記錄內部依據、搜尋字串、外部來源及節點紀錄。以 Node.js 混合題為例，`it-01` 政策寫明公司使用 Node.js 22，搜尋節點據此建立 `Node.js 22 official download site:nodejs.org`，不以模型猜測的版本取代內部規範。

## 二 實驗環境與資料

實驗於 Windows、Python 3.12.13 執行。主要套件版本為 LangGraph 1.1.10、LangChain 1.2.17、ChromaDB 1.5.9、langchain-mcp-adapters 0.2.2 及 Gradio 6.14.0。模型設定為 NVIDIA `nvidia/nemotron-3-super-120b-a12b`；向量嵌入使用本機 `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`。公開搜尋透過 Tavily 遠端 MCP 的 `tavily_search` 工具執行。憑證由專案外部 `.env` 載入，實驗紀錄不包含金鑰。

知識庫由 `knowledge.json` 載入，五類各十筆，共 50 筆：人資與工作規範、資訊與開發環境、資訊安全、員工到職、行政與內部流程。每筆包含來源 ID、標題、分類與內容。Chroma 使用記憶體內索引，每次啟動重新建立。這是示範資料，不代表任何真實公司的政策。

## 三 測試方法與判讀標準

可控測試以替身 LLM、向量庫與 MCP 工具執行真正的節點和圖連線，核對路由、相關性分支、Node.js 版本傳遞、Docker 與加班查詢、查詢重試、fallback、Tavily 無金鑰或連線失敗，以及網址驗證。這些測試驗證程式控制流程，不能代表模型服務可用率或回答事實正確率。

真實服務實測使用 `onboarding_runner.py` 所列六題，每題記錄路由、評分、重試次數、外部搜尋是否呼叫、來源 URL、節點 trace、回答與耗時。第一輪失敗題再獨立重跑一次。完成定義為圖回傳最終 State；這不等於回答每一句都經人工查證。

## 四 結果

### 四之一 可控測試與基礎連線

14 項 `unittest` 全數通過。真實 Chroma 成功建立 50 筆索引，Node.js 版本查詢首筆為 `it-01`；真實 Tavily MCP 可回傳五個 `nodejs.org` 網址；Gradio 本機首頁曾回應 HTTP 200。這些檢查分別確認索引、工具連線及介面可啟動，並不涵蓋六題端到端的全部結果。

### 四之二 六題真實服務實測

| 題號 | 問題摘要 | 預期路徑 | 第一輪觀察 | 重跑結果 |
|---|---|---|---|---|
| 1 | 公司遠端工作政策 | internal | 完成；檢索含 `hr-06`，評分 relevant，沒有外部搜尋 | 未重跑 |
| 2 | Node.js 官方最新 LTS | external | 完成；呼叫 Tavily，取得 5 個 `nodejs.org` URL | 未重跑 |
| 3 | 公司 Node.js 版本與官方下載網址 | hybrid | NVIDIA 模型呼叫回傳 503，未得到本輪完整 State | 再次 503 |
| 4 | 新人 Docker 學習與官方教學 | hybrid | NVIDIA 模型呼叫回傳 503，未得到本輪完整 State | 再次 503 |
| 5 | 公司加班規定與臺灣公開法規 | hybrid | 完成；內部 `hr-04`、外部 5 個官方網域 URL；回答末段截斷 | 未重跑 |
| 6 | 公司是否允許 telecommuting | internal | NVIDIA 模型呼叫回傳 503，未觀察到真實改寫流程 | 再次 503 |

第一輪 19:59:38 至 20:01:00，三題完成、三題失敗。失敗三題於 20:01:36 至 20:01:56 重跑，均再次收到 `Service temporarily overloaded`、HTTP 503。此錯誤發生於設定的 NVIDIA `nvidia/nemotron-3-super-120b-a12b` 模型服務呼叫；它與本機 Chroma 及 Tavily MCP 搜尋錯誤不同。同一輪中第 1、2、5 題仍成功，說明當時是間歇性服務問題，不能由本次觀察推定端點長期不可用。

完成案例的 trace 與預期路徑一致：第 1 題為 internal 檢索與生成，第 2 題為 external 搜尋與生成，第 5 題為 hybrid 檢索、評分、搜尋與生成。第 5 題正確分開「公司內部規範」和「外部公開資訊」，但模型輸出末段截斷，故內容完整性未通過人工檢視。

第 2 題的「最新 LTS」版本是當次模型根據搜尋摘要產生的答案；本實驗沒有逐頁核對官方發布頁，不能把它作為獨立驗證的最新版本結論。

開發階段另曾有一筆 Node.js 混合題完成全路徑，檢索到 `it-01`、形成 `Node.js 22 official download site:nodejs.org`，並取得五個 Tavily 來源；這項觀察未納入上述六題同批次統計。本次六題批次的第 3 題仍記為失敗。

## 五 討論與限制

可控測試證實 Retry Loop、路由與 MCP 交接在指定輸入下正常；真實模型路由和評分仍會受輸出與服務狀態影響。英文 `telecommuting` 題在替身測試中會經一次改寫，但本次真實呼叫於進入可觀察流程前收到 503，不能聲稱真實模型已完成改寫。

目前程式對 LLM 呼叫設有簡短重試；本次 503 仍未被排除。對外部「最新」資訊，Tavily 結果與模型摘要需要再核對原始官方頁。加班題回答末段截斷，表示即使圖走到 `generate`，也需要完整性檢查。知識庫為小型虛構資料，無真實企業文件的權限管理、更新治理或資料洩漏評估。Chroma 索引不持久化，啟動時須重新嵌入。

## 六 結論與重現方式

本實驗完成三路 Router、Corrective RAG 回圈與 Tavily MCP 的整合，並以 14 項可控測試驗證圖邏輯。真實服務可完成 internal、external 及 hybrid 各一種案例，但六題同批次成功率為 3/6；另三題在兩次嘗試中均遇到 NVIDIA 503。下一步應先處理線上模型的服務不穩定與長答案截斷，再進行多輪、逐頁來源核對的回答品質評估。

於專案資料夾執行測試與重現實測：

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
$env:ONBOARDBOT_ENV_FILE = 'C:\Users\blue\我的雲端硬碟\OneDrive_OneDrive_Backup\北科電子工程系碩士班_黃士嘉老師\TrainingProcess\Original\TOPIC\.env'
.\.venv\Scripts\python.exe experiments\run_live_demos.py
```

實測原始紀錄位於 `experiments/live_demo_results.json` 與 `experiments/live_demo_retry_results.json`。實作與測試見 `graph.py`、`nodes.py`、`knowledge.json`、`tests/test_workflow.py`。架構來源為 [原版 OnboardBot](https://github.com/shafiqul-islam-sumon/langgraph/tree/main/advanced-3-rag-conditional-routing)；工具連接參照 [Tavily MCP 官方專案](https://github.com/tavily-ai/tavily-mcp)與 [LangChain MCP adapters](https://github.com/langchain-ai/langchain-mcp-adapters)。
