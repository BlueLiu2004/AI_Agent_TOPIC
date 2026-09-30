# OnboardBot 三分鐘架構教學分鏡

## 製作前的 repository 解讀

教學對象懂 Python，尚不熟悉 LangGraph、Corrective RAG、MCP。本片從資料需求與 State 的改變教起。以目前 Python 原始碼為事實依據，影片不連線呼叫模型或 Tavily，不載入 .env。TechCore 與 50 筆政策均為虛構示範。

- 入口：onboarding_runner.py 的 ask_with_trace 建立初始 State，呼叫 compiled_graph.ainvoke。
- State：original_question 保留原句；question 可改寫；Node 回傳欄位更新，由圖合併。route、documents、doc_grade、retry_count、internal_context、web_query、web_urls、final_answer、trace 是本片關注欄位。messages 另有 add_messages reducer。
- Graph：graph.py 登記 8 個節點。路由三選一；external 直接進 build_web_query。internal/hybrid 先檢索並評分。相關時 internal 回答，hybrid 搜尋；不相關且尚有次數則 rewrite_query → retrieve；耗盡則 fallback_generate。
- 檢索：knowledge_base.py 把 knowledge.json 的 50 筆政策建立成記憶體內 Chroma。retrieve_node 寫 documents；grade_documents_node 才在 relevant 時寫 internal_context。不能把檢索完成與評分完成混為一談。
- 混合查詢：nodes.py 以正規表示式從 internal_context 取 Node.js 主版本；本例 it-01 指定完整版本 22.11.0，擷取主版本 22，再建立 Node.js 22 official download site:nodejs.org。缺少版本時可能走一般 query LLM；程式不是全面證明任意未知版本絕不被猜測。
- MCP：tavily_search_node 使用 MultiServerMCPClient 取得遠端工具，只呼叫 tavily_search。沒有額外 tavily_extract 節點。官方網域限制依問題關鍵詞建立，正常 JSON 解析結果再以 hostname 或子網域過濾；非 JSON fallback 的 URL 解析沒有相同的第二次網域過濾。
- 生成：prompt 要求 hybrid 分開內部規範與公開資訊；generate_node 把辨識到但不在 web_urls 的 URL 換成來源提示，再附上搜尋 URL。這是來源一致性限制，不是頁面最新性、正確性或語意相關性的保證。
- 模型：llm.py 包裝 NVIDIA 或 Gemini；NVIDIA 的 JSON 模式搭配 Pydantic。不是影片製作依賴，不在製作中呼叫。
- 測試：tests/test_workflow.py 使用 fake LLM/vector/MCP，14 個測試驗證真正的圖連線與節點行為。corrective_retry 固定示範 internal → 一次改寫 → relevant。
- 實驗：09/24 同批六題 3 completed、3 模型 503；09/25 六題皆 completed，但 telecommuting 被分類 hybrid，Node.js 與 Docker 搜尋來源仍有品質問題。影片不把 completed 等同事實正確。

## 三條教學故事線

1. 資料要去哪裡找：Router、Node、Edge、Conditional Edge 與 State。
2. Node.js 22 的旅程：從 it-01 到 documents，再到 internal_context、web_query、web_urls、final_answer。
3. 找不到或找到不好的資料時：Corrective RAG 回圈、重試上限、fallback，最後看測試能與不能證明什麼。

## 時間軸與分鏡

| 場景 | 秒數 | 畫面與動作 | 觀眾學會什麼 |
|---|---|---|---|
| 1 提問 | 0–12 | 問題卡，公司資料與公開網路兩區匯入回答 | 一題可能需要兩種來源 |
| 2 全貌 | 12–34 | 簡圖逐一點亮 internal / external / hybrid；搭配三個實際 Demo 問句 | 路由是來源選擇；Node 處理、Edge 連接 |
| 3 State | 34–54 | 真實 state.py 11 行程式碼，右側 State inspector；接著揭示 conditional edge 片段 | 原句不變、question 可變；條件連線依 State 選路 |
| 4 Hybrid 主角 | 54–100 | 左侧圖逐步點亮；右側從 documents 到 internal_context，22 的資料標記移入 web_query，再出現搜尋來源與兩段式回答 | 版本來自內部政策，搜尋依賴內部結果 |
| 5 修正檢索 | 100–132 | 固定標示「可控測試示範」；telecommuting → not_relevant → rewrite → 遠端工作政策 → retrieve；retry 0→1；再說明上限 | 看得到真正的回圈與終止條件 |
| 6 工具與來源 | 132–156 | MCP 取得工具流程；官方網域；generate_node 的真實 URL 比對片段 | 工具協定、来源分工及驗證能力邊界 |
| 7 測試與現實 | 156–178 | 14 項控制流程測試；09/24 3/6、09/25 6/6；品質问题提示 | 流程成功不保證回答正確 |
| 8 回顧 | 178–192 | 重新展示完整真實圖與三個 takeaway；建議閱讀顺序 | 沿 State 追一題，理解設計 |

## 畫面與聲音規則

- 1920×1080、30 fps、192 秒。自包含 Remotion project。
- 深色技術資訊圖；內部青綠、外部藍色、hybrid 琥珀色，語意色固定。
- 2–3 個主要資訊區。程式碼只用從 repository 逐行抽出的真實片段，4–14 行，帶檔名及行號。
- 主要文字 32–58 px、程式碼約 24–28 px、字幕 36 px；底部保留字幕安全區。
- 以節點高亮、箭頭與資料標記移動呈現因果；不使用素材照、卡通或裝飾性 AI 圖。
- 場景 4 的 internal_context 必須在 grade relevant 之後才出現。場景 5 的圖是控制測試，不偽稱 09/25 的真實分類結果。
- 使用 Windows 本機 zh-TW TTS，無線上 TTS；可編輯 narration 與逐句 SRT 同源。字幕獨立足以理解。

## 觀察與界線

原應用可能誤分路由、只做文件組整體評分、官方網域仍可能回傳舊或不相關頁面；目前 URL 檢查也不是完備的事實驗證。影片說明這些限制，不修改原应用。工作開始時既有的 .env.example 刪除與 AI_Agent_TOPIC.tar 未追蹤檔不屬於本任務。

## Render 前的事實查核

- [x] 三種 route；external 不必查 Chroma；hybrid 先檢索。
- [x] original_question 與 question 分開，改寫增加 retry_count。
- [x] 回圈為 rewrite_query → retrieve；預設最多改寫兩次，相關性判斷優先於重試耗盡。
- [x] Tavily 工具從 MCP client 取得，不把 MCP 說成搜尋引擎。
- [x] it-01 明載 Node.js 22.11.0；查詢建構使用內部 context 的版本。
- [x] 網域過濾及 URL 比對按目前實作說明，沒有「杜絕幻覺」宣稱。
- [x] 不把虛構政策當真實企業規章，不把測試通過當品質保證。
- [x] 已讀 README、state、graph、nodes、knowledge_base、llm、runner、tests、全部 prompts、中文實驗報告與三份實驗 JSON。

## 教學檢查

三路差異在場景 2；State 與原句/查詢差異在場景 3；版本来源與模型不可自行決定公司政策在場景 4；不相關處理在場景 5；MCP 職責在場景 6；測試能與不能驗證的範圍在場景 7。八個指定問題都有畫面與旁白對應。
