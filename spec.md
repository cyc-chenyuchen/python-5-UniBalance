# 校園改革模擬平台

## 1. 專案目標

讓學生把校園觀察轉成提案，透過 AI 訪談、客製方案與短回合模擬理解改革取捨，並保存可回顧的結果。

## 2. 問題與需求

### 目標使用者與待驗證問題

| 項目 | 說明 | 狀態 |
|---|---|---|
| 目標使用者 | 想反映校園問題，但可能不確定如何描述需求，或不知道改革方案會有哪些取捨的學生 | 專題假設，需訪談驗證 |
| 使用情境 | 學生觀察到校園生活、設施、服務或制度問題，想整理成具體提案 | 專題假設，需訪談驗證 |
| 預期困擾 | 既有反映方式未必能協助學生比較替代方案或預想資源、公平性等取捨 | 尚無使用者研究證據，不應當成已證實事實 |

目前尚未提供同學訪談或問卷結果。本專題應訪談至少 5 位同學，記錄原話並取得同意後再放入簡報；不得把此目標或預期效果描述成已完成的研究結果。

### 與常見方式的差異假設

下表比較的是工具類型的一般用途，不代表所有校內工具或 AI 產品都有相同功能。需透過實際使用者訪談確認差異是否重要。

| 做法 | 主要用途 | 本平台希望補足的體驗 |
|---|---|---|
| 意見箱／反映表單 | 收集問題或意見 | 透過訪談補充需求，並讓學生比較可行方向 |
| 問卷 | 彙整多人的回答 | 讓個別提案者看到方案間的遊戲取捨 |
| 一般 AI 聊天 | 開放式討論與文字建議 | 提供固定步驟的訪談、可選方案、兩回合決策及可回顧結果 |
| 一般模擬遊戲 | 練習情境中的決策 | 以玩家自己的校園提案生成情境；效果值經程式驗證並明確標為遊戲假設 |

### 使用者需求驗證計畫

訪談至少 5 位同學，確認：

1. 他們最近觀察到的校園問題，以及目前會如何反映。
2. 整理提案或理解方案取捨時遇到的困難。
3. 試玩後是否更能說明所選方案的取捨，以及是否願意把結果提供給學生會或相關單位參考。

保留匿名化原話、訪談日期及同意紀錄。未完成前，簡報應標示「待驗證」，不宣稱已找到普遍痛點。

## 3. 功能與狀態

| 功能 | 目前程式行為 | 狀態 |
|---|---|---|
| 校園提案 | 接受 1～300 字提案；首頁提醒勿輸入個人資料 | 已實作 |
| AI 訪談 | Gemini 根據提案與先前回答逐題生成問題，每題提供 2～4 個選項；流程固定兩題 | 已實作 |
| 客製方案 | Gemini 產生兩個方案、策略、描述、理由與效果值 | 已實作 |
| 客製模擬 | Gemini 產生兩個事件，每回合兩個行動選項 | 已實作 |
| 結算回顧 | 顯示指標、分數、固定評語與根據已存紀錄組成的回顧 | 已實作 |
| 歷史結果 | 瀏覽本機 `records.json` 中的紀錄，並可查看有新格式 `record_id` 的結果卡 | 已實作 |
| 離線 Demo | 設定 `DEMO_MODE=1` 後使用明確標示的預設示範回覆，不呼叫 Gemini | 已實作 |
| 公開交流 | 帳號、留言、公開公告欄、分享連結及多人協作 | 尚未實作 |
| 真實改革追蹤 | 追蹤提案是否提交、採納或改善校園 | 尚未實作 |

AI 被要求支援校園生活、校園成員、設施、服務與制度相關提案；只有模型判斷為明確非校園問題時才拒絕。這是模型判斷，不能保證所有輸入都一定被正確分類或成功生成。

## 4. 影響力與成果表達

### 目前可展示的成果

- 使用者輸入提案、完成兩題訪談、選擇方案、完成兩回合並查看結果卡。
- 每筆完成結果保存在本機 JSON，並可於歷史結果頁瀏覽。
- 遊戲指標、分數及選擇可作為「模擬中的取捨」展示，不代表真實政策效果。

目前尚未將結果送交學生會或校方，也沒有量測校園問題是否實際改善。不得把遊戲分數、提案數量或紀錄數量直接宣稱為校園影響力。

### 後續測量計畫

試用前後以簡短問題詢問使用者：

- 試玩後能否說出所選方案的一項優點和一項取捨。
- 是否願意把結果交給學生會或相關單位參考，以及原因。
- 哪個訪談問題、方案或模擬事件最有幫助／最不符合需求。

只有在實際收集資料後才報告人數或比例；同時記錄試用方式與問題，不預先編造效果數字。若要主張實際校園改善，需另行追蹤提案是否提交、是否採納及可觀察的改善證據。

## 5. 技術、隱私與 Demo

### 技術設定

- Python、Flask、Jinja templates、HTML 表單。
- 使用 `requests` 呼叫 Gemini `generateContent` REST API，不使用 Gemini SDK，也不自行訓練模型。
- 套件需求：Flask 3.x、requests 2.x。
- 必須設定環境變數：
  - `GEMINI_API_KEY`：Gemini API 金鑰。
  - `GEMINI_MODEL`：Gemini 模型 ID。
  - `FLASK_SECRET_KEY`：Flask session 簽章金鑰。
- 設定 `DEMO_MODE=1` 可啟用離線示範；頁面會標示「離線示範模式」，其內容是固定示範資料，不是 AI 即時生成，也不應用來展示客製化能力。
- Flask session 只保存流程識別碼及最近結果識別碼；完整訪談和遊戲狀態存於伺服器程序的記憶體字典。伺服器重啟會使未完成流程失效。
- 程式邏輯以基礎變數、`if`、`for`、函式、list、dict 及 JSON 檔案讀寫為主；重要註解使用中文。

### Gemini 呼叫與等待時間

- 單次 HTTP 嘗試使用 `timeout=(2, 6)` 秒，分別代表 connect/read timeout。
- 每個 Gemini 請求最多嘗試 3 次（首次呼叫加 2 次重試），只對 HTTP 503 與 timeout 重試，等待間隔為 2 秒及 4 秒。
- 依設定的 timeout 加上重試等待計算，單次請求最多約 30 秒；這不是作業系統層級的絕對牆鐘時間保證，DNS 或網路堆疊可能造成額外耗時。
- 正常線上流程最多會呼叫兩次訪談、一次方案生成及一次結果回顧；依設定值估算，全部請求約 120 秒，加上頁面操作時間可能超過 3 分鐘。
- Demo 前應實際確認網路與 API 金鑰。若網路不可用，使用 `DEMO_MODE=1` 完成流程；建議另錄製一支成功完成的 Demo 影片。影片尚未放入本專案。

### 隱私與資料保存

- 會傳送給 Gemini：
  - 訪談請求：提案及先前訪談回答。
  - 方案請求：提案、兩題回答及通用遊戲指標設定。
  - 結果回顧請求：最終指標、所選方案名稱／策略及玩家兩回合行動。
- 不會將訪談回答寫入 `records.json`。
- 本機 `data/records.json` 會明文保存提案、所選方案、效果值、玩家行動、指標、分數與回顧；檔案不會由本程式自動上傳或公開。
- 首頁明確提醒勿輸入姓名、電話、學號等個人資料。Demo 或研究引用原話前須先匿名化並取得同意。
- 本機 JSON 紀錄沒有加密、帳號權限或多人同時寫入控制，不應保存敏感資訊。

## 6. AI 輸入、輸出及驗證

### 訪談

`ask_interview_question(proposal, answers)` 預期回傳：

```json
{
  "question": "你最希望先改善哪個部分？",
  "options": ["改善使用流程", "增加可用資源"]
}
```

程式驗證問題為非空字串，且選項為 2～4 個非空字串；Flask 流程固定提問兩次。

### 方案與模擬回合

`recommend_plans(proposal, answers, game_config)` 預期回傳 `scenario_title`、恰好兩個 `recommendations` 及恰好兩個 `rounds`。每個方案包含標題、策略、描述、理由及效果值；每個回合包含事件及兩個行動選項。每個行動選項包含文字和四項效果值。

明確非校園提案回傳：

```json
{
  "supported": false,
  "scenario_title": "",
  "recommendations": [],
  "rounds": []
}
```

程式驗證方案數、回合數、每回合選項數、文字長度、完全重複策略、效果欄位與數值範圍。Python 產生方案、回合及選項 ID。策略相異檢查只比較去除前後空白並轉小寫後的完整字串，無法辨識語意近似。

| 文字欄位 | 長度上限 |
|---|---:|
| 情境名稱 | 30 字元 |
| 方案標題 | 30 字元 |
| 方案策略 | 24 字元 |
| 方案描述、推薦理由 | 各 90 字元 |
| 回合事件 | 100 字元 |
| 行動文字 | 70 字元 |

效果必須是整數（不接受布林值），且效果 dict 必須恰好包含下列四項：

| 指標 | 方案效果範圍 | 行動效果範圍 |
|---|---:|---:|
| `budget_remaining` | -20～0 | -10～0 |
| `problem_improvement` | 0～20 | -5～10 |
| `satisfaction` | -10～10 | -5～5 |
| `fairness` | -10～10 | -5～5 |

效果值為 AI 生成的遊戲假設，不是真實政策預測。格式錯誤或超出範圍時顯示錯誤，不以固定方案替代。

### 結果回顧的防捏造設計

- `choose_review_focus(record)` 只將已記錄的最終指標、所選方案名稱／策略及兩回合行動交給 Gemini。
- Gemini 只回傳一個已存在的 `focus_metric` 及一個有效的 `action_index`；程式驗證這兩者確實存在於紀錄中。
- 顯示的回顧文字由 Python 組成，只引用已存的總分、指標值、方案名稱、事件及玩家行動，不使用 Gemini 自由生成的敘述。
- 若回顧請求失敗或欄位無效，使用最低最終指標及第一個已記錄行動產生回顧，並明確顯示回顧採用本機整理的提示。

## 7. 遊戲與計分規則

- `data/menu.json` 提供通用指標名稱及初始值；方案、事件及行動由 Gemini 依提案與回答產生。
- 開始模擬時先套用所選方案效果，再依序套用兩回合的行動效果。
- 每次套用後，四項指標各自限制在 0～100。
- 起始值目前皆為 75。總分為最終四項指標的平均值，使用 `int(total / count + 0.5)` 四捨五入。
- 計分邊界驗算（假設 Gemini 同時產生所有允許的效果極值）：
  - 最低：`[35, 65, 55, 55]`，平均 52.5，程式分數 53。
  - 最高：`[75, 100, 95, 95]`，平均 91.25，程式分數 91。
  - 因此目前「80 分以上」評語在規則範圍內可達成；此為數學邊界，不是實際玩家成績。
- 評語仍依分數區間使用三段固定文字（80 以上、60～79、低於 60）；結果回顧另依實際紀錄組成。

## 8. JSON 格式

### `data/menu.json`

只保存通用遊戲設定，不保存固定議題、方案、事件或行動。

```json
{
  "metric_labels": {
    "budget_remaining": "剩餘預算",
    "problem_improvement": "問題改善",
    "satisfaction": "學生滿意度",
    "fairness": "公平性"
  },
  "initial_metrics": {
    "budget_remaining": 75,
    "problem_improvement": 75,
    "satisfaction": 75,
    "fairness": 75
  }
}
```

### `data/records.json`

最外層是 JSON 陣列。完成第二回合時新增一筆紀錄，欄位包括：

| 欄位 | 說明 |
|---|---|
| `record_id` | 新紀錄的唯一識別碼，用於歷史結果頁連結 |
| `created_at` | 含時區的 ISO 格式時間 |
| `scenario_id` | 目前固定字串 `campus_custom`，只作相容／識別用途；實際情境以 `scenario_title` 為準 |
| `scenario_title` | AI 生成情境名稱 |
| `proposal` | 使用者提案 |
| `plan_id`、`plan_title`、`plan_strategy` | 所選方案識別碼、標題與策略 |
| `plan_description`、`plan_reason`、`plan_effects` | 所選方案作法、理由及效果值 |
| `initial_metrics`、`final_metrics`、`metric_labels` | 起始／最終指標及顯示名稱 |
| `actions` | 每回合的事件與玩家選項 |
| `total_score`、`comment` | 總分與固定評語 |
| `review`、`review_note` | 依已存數據組成的回顧及其來源提示 |

舊版紀錄可能沒有 `record_id` 或回顧欄位；歷史頁會顯示其可用資訊，但沒有識別碼的舊紀錄不會有結果卡連結。讀取損壞的 JSON 時顯示錯誤，不會以空資料覆蓋原檔。

## 9. 路由

| 路由 | 方法 | 功能 |
|---|---|---|
| `/` | GET | 提案輸入與隱私提醒 |
| `/interview/start` | POST | 驗證提案並開始訪談 |
| `/interview` | GET | 顯示訪談問題 |
| `/interview/answer` | POST | 驗證回答；兩題完成後生成方案與模擬 |
| `/interview/retry` | POST | 重試目前失敗的訪談或方案請求 |
| `/plans` | GET | 顯示兩個客製方案 |
| `/simulation/start` | POST | 驗證方案並開始模擬 |
| `/simulation` | GET | 顯示目前事件、選項及指標 |
| `/simulation/choose` | POST | 驗證行動、更新指標；完成時建立結果 |
| `/result` | GET | 顯示本次結果卡 |
| `/records` | GET | 顯示本機歷史結果清單 |
| `/records/<record_id>` | GET | 顯示有新格式識別碼的歷史結果卡 |
| `/reset` | POST | 清除目前流程並回首頁 |

只有 `show_result(record)` 呼叫 `save_record(record)`；結果頁重新整理不會重複寫入。

## 10. 驗收條件與測試

執行方式：在專案資料夾執行 `python tests.py`。測試會在匯入 Flask app 前設定測試用 `FLASK_SECRET_KEY`，使用 mock Gemini 回應，不會呼叫真實 API，也不會覆寫專案現有 `records.json`。

| 驗收案例 | 預期結果 | 自動測試 |
|---|---|---|
| 校園提案完成流程 | 訪談、方案、兩回合、結果及存檔均成功 | 300 字提案端到端測試 |
| 300 字提案及 cookie 大小 | 完整提案可走完，session cookie 小於 4096 bytes | `test_three_hundred_character_proposal_completes_without_large_cookie` |
| 非校園提案 | AI 回傳 `supported=false` 時不提供方案 | `test_non_campus_proposal_is_rejected_by_ai_result` |
| AI 回傳非 JSON | 顯示明確 JSON 格式錯誤 | `test_non_json_ai_response_is_rejected` |
| 效果值超出範圍 | 拒絕方案，不套用效果 | `test_out_of_range_effect_is_rejected` |
| `menu.json` 損壞 | 回報格式錯誤且原始檔內容不變 | `test_corrupt_menu_is_reported_without_overwriting_file` |
| `records.json` 損壞 | 回報格式錯誤且原始檔內容不變 | `test_corrupt_records_are_reported_without_overwriting_file` |
| 計分最低／最高案例 | 分別得到 53 與 91；最高能達到 80 分以上評語 | `SimulationScoreTests` |
| 重試次數與等待 | 單請求 3 次嘗試、間隔 2／4 秒，設定等待估算 30 秒 | `test_retry_attempt_count_and_delays_are_bounded` |
| 歷史結果 | 新紀錄出現在清單並能開啟結果卡 | 300 字端到端測試 |
| 離線 Demo | 不呼叫 Gemini，顯示離線模式標記 | `test_offline_demo_mode_completes_without_gemini_requests` |

此外，至少 5 位同學的需求訪談及試用後理解度／轉交意願屬於研究驗收，不是目前自動化測試或已取得的成效。

## 11. 檔案結構

```text
NCU/
├── app.py                 # Flask 路由、伺服器端遊戲狀態與存檔流程
├── ai_service.py          # Gemini API、重試、AI 輸出驗證與離線 Demo
├── simulation.py          # 效果套用、指標限制、計分與評語
├── storage.py             # menu.json、records.json 讀寫
├── tests.py               # 驗收及回歸測試
├── test.py                # 可選的 Gemini API 連線診斷腳本，非網站流程的一部分
├── requirements.txt       # Flask、requests 版本需求
├── spec.md                # 本規格
├── data/
│   ├── menu.json          # 共用指標名稱與起始值
│   └── records.json       # 本機結果紀錄
├── templates/
│   ├── base.html          # 共用版型、歷史連結及離線模式標記
│   ├── index.html         # 提案輸入及隱私提醒
│   ├── interview.html     # AI 訪談
│   ├── plans.html         # 方案選擇
│   ├── round.html         # 模擬回合
│   ├── result.html        # 結果卡及回顧
│   ├── records.html       # 歷史結果清單
│   └── error.html         # 錯誤與重試
└── static/
    └── style.css          # 頁面樣式
```

`test.py` 可單獨執行以直接測試 Gemini API 是否可連線；它不會被 `app.py` 或 `tests.py` 呼叫，且目前 URL 中的模型名稱是寫死的。網站的完整驗收應執行 `python tests.py`，不是 `python test.py`。

## 12. 主要函式

| 函式 | 輸入 | 責任 |
|---|---|---|
| `send_request` | URL、headers、request data | 呼叫 Gemini HTTP API，對 503／timeout 有上限地重試 |
| `_request_gemini` | system prompt、user prompt | 讀取環境變數、呼叫 Gemini 並處理 API 錯誤 |
| `_read_json_reply` | Gemini 回覆文字 | 解析並驗證 JSON 物件 |
| `ask_interview_question` | 提案、先前回答 list | 產生訪談題目；離線模式回傳預設題目 |
| `recommend_plans` | 提案、回答 list、遊戲設定 dict | 產生兩方案及兩回合；驗證輸出；離線模式回傳明確示範資料 |
| `_validate_text` | 文字、長度上限、錯誤訊息 | 驗證並整理文字 |
| `_validate_effects` | effects、允許範圍、錯誤訊息 | 驗證四項整數效果 |
| `choose_review_focus` | 完成的結果紀錄 | AI 選擇有效指標及行動索引；離線模式選擇最低指標 |
| `_get_game` | Flask session | 以流程 ID 取得伺服器端遊戲狀態 |
| `_make_review_text` | 結果紀錄、已驗證的焦點 | 只用紀錄中的事實組成回顧文字 |
| `_fallback_review_focus` | 結果紀錄 | AI 回顧失敗時選擇最低指標與第一個行動 |
| `apply_effects` | 目前指標、效果 dict | 套用效果並將值限制在 0～100 |
| `run_round_choice` | 目前指標、行動效果 | 套用單回合效果 |
| `calculate_total_score` | 最終指標 dict | 計算平均分數並四捨五入 |
| `make_comment` | 總分 | 回傳分數區間對應的固定評語 |
| `load_menu` | 無 | 讀取通用遊戲設定，損壞時顯示錯誤 |
| `load_records` | 無 | 讀取紀錄；檔案不存在時建立空陣列，損壞時顯示錯誤且不覆蓋 |
| `save_record` | 紀錄 dict | 將紀錄附加寫入 JSON |
| `show_result` | 完整紀錄 dict | 唯一呼叫 `save_record` 的流程函式，設定最近紀錄 ID 並導向結果頁 |
