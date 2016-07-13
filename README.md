# 倒GA：把 GA 的 Log Raw Data 抓出來再上傳到 BigQuery

## 運行方式
1. Copy sample_config.py to config.py
2. 修改 config.py 中的 PROJECT_ID, DATA_SET, VIEW_ID, DATE_INIT
3. 執行 DauGA.py (python2), 須提供credential的path, 此credential需要有google analytics跟google big query的權限


## 重要資源
Google提供的[Demo網站](https://ga-dev-tools.appspot.com/dimensions-metrics-explorer/)，這個真的很重要，但是有很難找，應該會有機會用到。


## 功能簡介
這個 Code 是根據 Blog 上面一篇[文章](http://daynebatten.com/2015/07/raw-data-google-analytics/)寫成的。 
文章的簡述了如何把 GA 裡面的 Raw Data Dump 出來，然後存進 BigQuery 裡面(這個功能如果由Google官方的服務來進行，一個月至少要付500美金，所以讓我們懷著感恩的心地使用這項功能吧。)

能夠做到這個功能的關鍵是，你跟 GA 藉由 [Report API](https://developers.google.com/admin-sdk/reports/v1/reference/) 所撈取出來的資料，每筆資料欄位都只對應到<b>一筆資料</b> -- 理論上，Report API希望你撈取的資料是經過統計計算的結果，舉例：每個縣市的不同類型使用者(新使用者、重複使用者)，在某方面(頁面停留時間or點擊次數or...)的統計結果，前者叫做 Dimension，後者叫做 Metrics，意思就是說，Report API report 給你不同 Dimension 下的 Metrics 統計結果。有關於不同的 Dimension 和 Metrics 介紹請看[這裡](https://developers.google.com/analytics/devguides/reporting/core/dimsmets)。

但是 Blog 裡面提供了一個厲害而簡單作法，GA 本身就有提供把自訂的 Customized Dimension 傳給 GA。如果我們傳給 GA 的 Customized Dimension 是完全不會重複的(ex. unique_user__id and timestamp)，我們跟 Report API request 資料的時候，它就會都把每一筆分開來，然後我們就可以拿到 GA log 的 Raw Data 了！！！

目前 Report API 提供 50000 次 request，每次上線 10000 筆，所以除非網站已經大到一天要 Log 5億筆資料，不然這個功能可以完全滿足我們的需求 --> 順利把 GA log 的 raw data request 出來然後上傳到 BigQuery 裡面，方便我們做各樣的分析。更棒的是，你可以順便把一些 GA 提供的很棒的使用者資料 (ex. 地區、使用系統、機型、瀏覽器)一併帶出來，供後續使用。


## 事前預備和程式執行方式
我們的目的是儘量自動化把資料重 GA dump 出來，然後自動化上傳到 BigQuery 形成我們需要的 Table，按時更新資料(把新的資料 append 到 BigQuery 上面)，讓我們以後只要負責開心在 BigQuery 裡面做資料分析就好了。


- 在執行 dauGA.py 之前需要準備好的注意事項...
- 先請上 [Google Cloud Platform](https://console.cloud.google.com/iam-admin/serviceaccounts/project) 申請你專屬的 Service Account，然後把檔案路徑 update 到 Code 的 CREDENTIAL_PATH 裡面。
- 安裝特殊的 pandas，因為目前的 pandas 不支援把 table append 不是它自己創造的 BigQuery table ([相關issue](https://github.com/pydata/pandas/issues/13086))，但是我們需要這項功能，因此先 Fork 一個 Pandas 出來，目前 issue 上表示會在下一版 (0.18.2) 修正這個問題。

```
   pip install git+https://github.com/junyiacademy/pandas.git@tmp_solution_to_append_existed_bq_table
```

- 視需要修改config.py的參數
- 裡面最重要的是 DATA_SET ，如果你是在 local 端執行，請務必改掉 DATA_SET 的參數，避免污染或破壞 BigQeury 上面我們真正在使用的 Table
- 如果你要新增屬於你自己的 table，請把你要新增的 table 加在 ga\_bq\_config 這個變數裡面，它決定了你要從 GA report api dump 哪些東西下來，最終上傳哪些資料。關於 report\_request 的寫法，可以參考[這裡](https://developers.google.com/analytics/devguides/reporting/core/v4/rest/v4/reports/batchGet)。另外還要指定 "destination\_table" (你想把檔案存取到 BigQuery 的哪個 Table)
- 機制概述：程式每次跑的時候，都會去到 {{DATA\_SET}}.upload\_progress\_log 的 Table 裡面，逐一去 check 從 2016-6-4(DATE_INIT) 到跑程式的前一天，每天每個要 update 的表格，是否有 "success" 的記錄，如果沒有，則把對應 table 裡面這一天的資料刪除(確定之後再次 load 資料的時候不會發生重複)，然後在把那一天的資料重新 dump 一次。以此來確定系統和資料的穩定性。
- 不論每次程式 Dump 資料的成功與否，都會再 Update 到 {{DATA\_SET}}.upload\_progress\_log，供之後程式 Dump 資料時做參考，或供工程師 Review。

## 測試方式
#### 整個功能最主要做的事情有 1. 把資料從 GA 抓出來 2. 把資料做一些調整 3. 把資料上傳到 BigQuery 4. 確保 Robustness

1. 可以在 function request\_df\_from\_ga 裡面去 check 你從 GA 抓下來的資料是否符合你在 ga\_bq\_config 裡面的設定
2. 把資料做調整的過程寫在 function columns\_conversion 裡面，你可以讀取 function 回傳的 dataframe 確保要準備上傳的 table 符合你的需要。
3. 最後在 table 成功上傳後，check BigQuery 上面相對應的 table 和你 local 端的 dataframe 是一致的。
4. Robustness 是最需要小心測試的部份，因為 Code 是預期每天自動跑的，又牽扯到很多 外部的API，發生錯誤是預期當中的事情，我們不會希望每次出問題所有的資料都毀了需要重新來過，最理想的狀況是，哪一次程式 fail 了，之後重跑的時候可以直接修正掉之前的錯誤。程式實作的方法寫在前面的<b>機制概述</b>裡面。
5. Robustness 測試的方法，是最重要的，目前的作法是在程式跑到不同階段 Raise Error，然後看 a. 會不會有殘缺的資料 upload 到 BigQuery?如果沒有，下次跑程式的時候這一天這個 table 的資料是不是還是會補上;如果有殘缺的資料上到 BigQuery，下次跑程式的時候是不是會先把殘缺的資料刪除掉。
6. Check {{DATA\_SET}}.upload\_progress\_log 裡面每個 table 每天成功資料所記錄的 uploaded_data_size 和相對應的 table ga_session_date 的 count 是否一樣，來確認有沒有重複或缺少 load 資料的情況。 

## Future Work

1. 目前上傳的 BrowserUTC time 本身是含有 milli-second 的資料，但是因為 pd.to_gbq function 似乎只會上傳到 second 而已，如果真的需要更高的 resolution，之後可以有兩個作法 a. 修改 Pandas, b. 改成上傳 string，之後再用 query 的方式處理。
2. ga_session_time & backup_date 其實都不是 UTC time，但是資料欄位裡面還是顯示是 utc ，但是目前看起來也不好調，很可能要動到 pandas，之後可以找機會來處理。 

## Contributors
- ENsu (Main)
- Microsheep
