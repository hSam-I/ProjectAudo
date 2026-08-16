# ProjectAudo

AI-destekli algoritmik trading bot/framework (Python). Şu an sadece Binance spot
verisiyle backtest/paper çalışıyor; canlı trading henüz yok.

## Gerçek çalıştırma akışı (main.py)

`app/main.py` tek gerçek CLI giriş noktası (`python -m app.main`). Ayrıca
`app/web/server.py` (FastAPI) `app/web/dashboard_data.py` üzerinden aynı pipeline'ı
tarayıcıda gösteriyor.

Kullanılan gerçek zincir:

```
BinanceProvider.fetch_ohlcv
  -> DataValidator.validate
  -> IndicatorEngine.calculate_all         (app/indicators/indicator_engine.py)
       -> EMA/RSI/ATR/MACD/ADX/Bollinger/VWAP/OBV/CCI/Ichimoku/Stochastic
       -> FeaturePipeline.build            (app/features/feature_pipeline.py)
            -> tüm indikatörleri TEKRAR hesaplar (bkz. "Bilinen sorunlar")
            -> FeatureEngine.build         (app/features/feature_engine.py)
  -> FeatureEngine.build                    (main.py bunu AYRICA tekrar çağırıyor, gereksiz/redundant)
  -> DecisionEngine().evaluate(df)          (app/decision/decision_engine.py)
       -> MarketRegimeDetector.detect
       -> strategy.generate_signal(df)      (app/strategy/registry.py -> get_strategy)
                                             VEYA settings.enable_voting=True ise
                                             DecisionEngine._vote(df) (bkz. "Dördüncü tur" madde 14)
       -> SignalScorer.score(df)            ("legacy" kural tabanlı skor)
       -> ScoreEngine.score(df)             (AI feature skoru, app/ai/score_engine.py)
       -> SignalFilter.filter(raw_signal, score)
  -> RiskManager (stop_loss / take_profit / risk_amount)
  -> Backtester().run(df)                   (app/backtesting/backtester.py, kendi içinde
                                              IndicatorEngine.calculate_all'ı TEKRAR çağırır)
  -> PerformanceAnalyzer                    (Sharpe/Sortino/CAGR/Calmar dahil, bkz. "Dördüncü tur" madde 11)
  -> TradeJournal / EquityReport / EquityChart / DrawdownChart / TradeDistributionChart
```

`main.py` artık 5 çalışma modu destekliyor (`python -m app.main [--walk-forward|--scan|
--multi-position|--live]`):
- (flagsiz) `main()` — yukarıdaki tek-sembol backtest zinciri, varsayılan davranış, değişmedi.
- `--walk-forward` — `run_walk_forward()`: `WalkForwardAnalyzer` pencereleri üzerinde
  aynı `Backtester`'ı tekrar tekrar çalıştırır, konsola özet basar (bkz. "Dördüncü tur" madde 13).
- `--scan` — `run_scan()`: `Scheduler().run_once()` üzerinden çoklu sembol ham sinyal
  taraması yapar (risk sizing/trade açma YOK, bkz. "Dördüncü tur" madde 13).
- `--multi-position` — `run_multi_position()`: `MultiDataProvider.fetch_all()` ile çekilen
  tüm `settings.symbols`'u `Backtester.run(market_data: dict)`'e verip TEK bir paylaşılan
  portföyle çoklu-sembol backtest çalıştırır (bkz. "Beşinci tur").
- `--live` — `run_live_paper_trading()`: `settings.symbols[0]` için süresiz canlı döngü,
  `settings.enable_live_paper_trading`'e göre ya sadece gözlem ya gerçek paper trading
  yapar (bkz. "Altıncı tur").

`Backtester.run()` her mum için `DecisionEngine.evaluate(history)` çağırıp
`PaperBroker` üzerinden pozisyon açıp kapatıyor; risk tarafında
`PortfolioRiskManager`, `PositionManager`, `PositionSizer`, `RiskManager`
kullanılıyor (bunlar `app/risk/`, `app/backtesting/portfolio.py` — `app/portfolio/`
DEĞİL, aşağıya bak).

`MarketScanner` (`app/scanner/market_scanner.py`) ve `MultiAssetBacktester`
(`app/backtesting/multi_asset_backtester.py`) main.py tarafından kullanılmıyor,
ama kod olarak birbirine bağlı: `MultiAssetBacktester.scan()` ->
`MultiDataProvider.fetch_all()` (ham OHLCV) -> `MarketScanner.scan()` ->
her sembol için `IndicatorEngine.calculate_all(df)` sonra `DecisionEngine.evaluate(df)`
(bu çağrı 2026-08-10'da eklendi, bkz. Bilinen Sorun #1 — düzeltildi).

## Klasör yapısı (app/)

Ana pipeline'a bağlı olanlar:
- `data/` — `BinanceProvider` (ccxt), `MultiDataProvider`, `DataValidator`, `models.py`,
  `exceptions.py` (`DataProviderError`, 2026-08-11 eklendi, bkz. "İkinci tur" madde 6).
  `BinanceProvider` artık ccxt'nin kendi rate-limit throttling'ini de açıyor
  (bkz. "Üçüncü tur" madde 9).
- `indicators/` — EMA/RSI/ATR/MACD/ADX/Bollinger/VWAP/OBV/CCI/Ichimoku/Stochastic +
  `IndicatorEngine` (merkezi orkestratör)
- `features/` — `FeatureEngine` (trend/momentum/volatility/volume/pattern/market
  feature'ları üretir) + `FeaturePipeline` (indikatör + feature'ları birlikte üretir,
  `IndicatorEngine.prepare` içinden çağrılır)
- `strategy/` — `BaseStrategy` + `ema_rsi`, `breakout`, `trend_following`,
  `mean_reversion` stratejileri, `registry.get_strategy(name)` ile seçiliyor
  (`strategy_factory.py` ve `strategy_selector_v2.py` registry'nin dışında, kullanılmıyor)
- `decision/` — `DecisionEngine` (asıl orkestratör), `SignalScorer` (legacy skor),
  `SignalFilter`, `ai_decision_engine.py` (DecisionEngine'i saran ince bir wrapper,
  kendisi hiçbir yerden çağrılmıyor)
- `ai/` — `ScoreEngine` + `FEATURE_WEIGHTS` (weights.py). `confidence.py`,
  `market_regime.py`, `risk_adjuster.py`, `scoring.py`, `strategy_selector.py`,
  `trade_filter.py`, `features.py` bu dosyalar da `ai/` altında ama DecisionEngine
  bunların hiçbirini import etmiyor — sadece `score_engine.py` ve `weights.py` canlı.
- `market/` — `MarketRegime` enum + `MarketRegimeDetector` (DecisionEngine kullanıyor)
- `risk/` — `RiskManager`, `PositionSizer`, `PositionManager`, `PortfolioRiskManager`,
  `trailing_stop.py`, `break_even.py`, `partial_take_profit.py`
- `backtesting/` — `Backtester` (asıl), `Portfolio`, `Trade`, `PerformanceAnalyzer`
  (`performance.py`). `multi_asset_backtester.py` main.py'ye bağlı değil (yukarı bak).
  `backtest_runner.py`, `performance_report.py` kullanılmıyor. `Backtester` artık
  `app/portfolio/portfolio_manager.py::PortfolioManager`'ı da kullanıyor (sembol bazlı
  "açık pozisyon var mı" kapısı — bkz. "Beşinci tur"), bu yüzden `PortfolioManager`
  ARTIK YETİM DEĞİL (aşağıdaki "Tamamen yetim" listesine bak, güncellendi).
- `broker/` — `PaperBroker` -> `ExecutionEngine` (`fee_model.py` + `slippage_model.py`
  gerçekten uygulanıyor, her buy/sell'de fee bakiyeden düşülüyor ve fiyata slippage
  ekleniyor/çıkarılıyor). `Backtester` bu oranları `settings.commission`/`settings.slippage`'dan
  besliyor (2026-08-11'de düzeltildi, bkz. aşağı). Çıkışta (sell) slippage'in
  `trade.profit`'e yansımaması ayrı bir bug'dı, ayrıca düzeltildi (bkz. "Üçüncü tur" madde 7).
- `reporting/` — main.py'nin çağırdığı `TradeJournal`, `EquityReport`, `EquityChart`,
  `DrawdownChart`, `TradeDistributionChart`. Diğer dosyalar (`performance.py`,
  `performance_report.py`, `profit_factor.py`, `expectancy.py`, `average_trade.py`,
  `report_builder.py`) kullanılmıyor. `TradeDistributionChart` sıfır trade'de çöküyordu,
  düzeltildi (bkz. "Üçüncü tur" madde 8).
- `web/` — FastAPI dashboard (`server.py`, `dashboard_data.py`, `charts.py`)
- `config/` — `pydantic-settings` tabanlı `Settings` (`.env`'den okur)
- `core/` — `enums.py` (Signal/OrderSide/PositionSide/OrderType/OrderStatus),
  `indicator_accessor.py` (SignalScorer'ın indikatör okuma yardımcı sınıfı)
- `logging/` — `logger.py`
- `scanner/` — `MarketScanner` (main.py'ye bağlı değil, sadece `MultiAssetBacktester`
  üzerinden erişilebilir, o da hiçbir yerden çağrılmıyor)
- `execution/` — `order.py`, `order_book.py` (hâlâ dolaylı kullanılıyor —
  `PaperBroker.execute_buy()` bir `Order` oluşturup dolduruyor ama pending-order/limit-order
  yolu hiç tetiklenmiyor, backtest her zaman anlık market fill kullanıyor).
  `live_feed.py`, `live_trader.py`, `live_state_store.py` — `--live` CLI modu, bkz. "Altıncı tur".

**Opsiyonel/flag ile bağlı (Dördüncü tur, 2026-08-11 — main.py'ye artık bağlı ama
varsayılan davranışı DEĞİŞTİRMİYOR, hepsi opt-in):**

- `app/backtesting/performance.py::PerformanceAnalyzer` üzerinden HER ZAMAN (flag
  gerekmeden) bağlı: `app/analytics/sharpe_ratio.py`, `sortino_ratio.py`,
  `calmar_ratio.py` — `sharpe_ratio()`/`sortino_ratio()`/`cagr()`/`calmar_ratio()`
  metodları eklendi, main.py konsol raporuna basılıyor. Saf raporlama, karar/trade
  mantığına dokunmuyor (bkz. madde 11).
- `settings.enable_research` (varsayılan `False`) ile main.py'ye bağlı:
  `app/research/research_engine.py::ResearchEngine` (kendi içinde
  `app/optimization/{optimization_pipeline,scenario_runner,monte_carlo,risk_of_ruin}`
  kullanıyor) + `app/research/report_builder.py::ResearchReportBuilder` — backtest
  sonrası `reports/research_report.json` üretiyor (bkz. madde 12).
- `python -m app.main --walk-forward` ile main.py'ye bağlı:
  `app/optimization/walk_forward.py::WalkForwardAnalyzer` — `main.run_walk_forward()`
  üretilen her pencerede mevcut `Backtester`'ı çağırıyor (bkz. madde 12).
- `python -m app.main --scan` ile main.py'ye bağlı: `app/scheduler/scheduler.py::Scheduler`
  (zaten birbirine bağlı `app/backtesting/multi_asset_backtester.py::MultiAssetBacktester`
  -> `app/data/multi_data_provider.py::MultiDataProvider` -> `app/scanner/market_scanner.py::MarketScanner`
  zincirini çağırıyor) — risk sizing/trade açma YOK, sadece ham `Decision` per sembol
  (bkz. madde 13).
- `settings.enable_voting` (varsayılan `False`) ile `DecisionEngine.evaluate()`'e bağlı:
  `app/voting/{strategy_vote.py,voting_engine.py}` + `app/analytics/{learning_engine.py,
  weight_manager.py,strategy_stats.py,performance_db.py}` — `DecisionEngine._vote(df)`
  `settings.voting_strategies`'teki her stratejiyi `WeightManager`'dan gelen geçmiş
  win-rate ağırlığıyla oylatıp `VotingEngine.vote()` ile birleştiriyor;
  `Backtester._register_learning()` trade kapanınca SADECE kazanan taraftaki
  stratejilere `LearningEngine.register_trade()` çağırıyor (bkz. madde 14 — bu turun
  en riskli/invaziv adımı, DecisionEngine/Backtester çekirdeğine dokunuyor, bu yüzden
  varsayılan kapalı).

**Tamamen yetim (main.py'den hiçbir zincirle ulaşılamıyor, sadece kendi testleri var):**

- `app/agents/` — neredeyse boş, sadece `__init__.py` var, hiç sınıf yok. README'deki
  "Multi-Agent Analysis" vizyonunun henüz yazılmamış iskeleti.
- `app/portfolio/portfolio_manager.py::PortfolioManager` — **ARTIK YETİM DEĞİL.** "Dördüncü tur"
  madde 15'te (2026-08-11) "Backtester tek-sembol/tek-trade mimarisinde, entegrasyon ayrı bir
  proje" gerekçesiyle ERTELENMİŞTİ; tam da o ayrı proje "Beşinci tur"da yapılıp `Backtester`
  çoklu-sembol/çoklu-pozisyona genişletildi ve `PortfolioManager` bu genişlemede gerçekten
  entegre edildi (bkz. "Beşinci tur"). `app/backtesting/portfolio.py`'deki (bakiye/equity
  takip eden, gerçekten kullanılan) `Portfolio` sınıfıyla KARIŞTIRMA — isim çakışması var
  ama ayrı, tamamlayıcı sınıflar (`Portfolio`=bakiye, `PortfolioManager`=sembol bazlı
  "açık pozisyon var mı" kapısı).
- `app/portfolio/{risk_analyzer,risk_limits,statistics,performance_tracker}.py` — HÂLÂ YETİM.
  "Beşinci tur"da bilinçli olarak entegre edilmedi: `risk_limits.py::RiskLimits`
  `app/risk/portfolio_risk_manager.py::PortfolioRiskManager` ile aynı işi yapıyor (toplam risk +
  pozisyon sayısı limiti), iki paralel implementasyon istenmedi; diğer üçü `PerformanceAnalyzer`
  ile örtüşen raporlama yardımcıları.
- `app/position/Position` — HÂLÂ YETİM. `app/backtesting/trade.py::Trade`'in strict alt
  kümesi (sadece symbol/side/entry_price/quantity, stop_loss/take_profit/profit/status yok) —
  entegre etmenin hiçbir kazancı yok, "Beşinci tur"da da dokunulmadı.
- `app/services/market_analyzer.py` — round-1 taramasında kaçırılmış ekstra bir yetim
  modül (2026-08-11'de fark edildi). `app/services/__init__.py` bile yok. `MarketAnalyzer.analyze()`
  main.py'den bağımsız kendi `BinanceProvider`+`DataValidator`+`EMARSIStrategy`+`SignalScorer`+`RiskManager`
  zincirini kuruyor, hiçbir yerden çağrılmıyor.

Özet: "Dördüncü tur"da `voting` + `analytics` (weight_manager/learning_engine) birlikte
"geçmiş performansa göre strateji ağırlıklandırma" özelliğini `enable_voting` flag'i
arkasında main.py'ye bağlandı; `research` + `optimization` birlikte "parametre
optimizasyonu / senaryo analizi" özelliğini `enable_research`/`--walk-forward` arkasında
bağlandı; `scheduler` (+ zaten birbirine bağlı `multi_asset_backtester`/`market_scanner`/
`multi_data_provider`) `--scan` arkasında bağlandı. `agents`, `portfolio`, `position`
hâlâ tamamen yetim (yukarıya bak).

## Test durumu

`tests/` ~160 dosya, her modül (kullanılan/kullanılmayan fark etmeksizin) için ayrı
testi var; testler modülleri izole çağırıyor.

`tests/test_end_to_end.py` (2026-08-11 eklendi) main.py'nin gerçek zincirini
(`DataValidator.validate` -> `IndicatorEngine.calculate_all` -> `DecisionEngine.evaluate`
-> `RiskManager` -> `Backtester().run()` -> `PerformanceAnalyzer`) sabit/deterministik
sentetik OHLCV verisiyle uçtan uca çalıştırıp en az 1 trade açılıp kapandığını, equity
curve'ün (`balance_history`) tutarlı olduğunu (ilk değer `initial_balance`, hepsi finite,
uzunluk = kapanan trade sayısı + 1) ve performans metriklerinin makul aralıkta kaldığını
doğruluyor. Veri 4 fazlı kurgulandı (downtrend -> RSI'ı taşırmayan salınımlı yükseliş ->
güçlü rally -> keskin düşüş) çünkü `EMARSIStrategy` crossover anında `rsi < 70` şartını
arıyor; rastgele/gürültülü fiyat serilerinde crossover neredeyse hep RSI>70'te oluşuyor
ve hiç BUY tetiklenmiyordu (bu yüzden test verisi random değil, deterministik).

`tests/test_ema_rsi_walk_forward.py` (2026-08-11 eklendi) `ema_rsi` stratejisini 8 farklı
rejimden (uptrend/chop/downtrend/high-vol chop/güçlü hareketler) oluşan deterministik
(`seed=123`) sentetik veride `app/optimization/walk_forward.py::WalkForwardAnalyzer`
(train=250, test=100 mum) ile üretilen rolling pencerelerde tek tek backtest ediyor.
ÖNEMLİ BULGU: `ema_rsi`'nin fit edilebilir parametresi yok (EMA20/50 + RSI eşiği sabit
kodlanmış), o yüzden bu klasik "train'de optimize et, test'te doğrula" walk-forward'u
DEĞİL — rejim-sağlamlığı kontrolü. Sonuç: 7 pencereden 3'ünde train'de, 6'sında test'te
HİÇ TRADE açılmadı (toplam 7 pencerede sadece 7 trade). Yani strateji varsayılan
ayarlarla (BUY_THRESHOLD=60, minimum_confidence vb.) çoğu piyasa koşulunda tamamen
sessiz kalıyor; item-1'deki e2e testin trade üretmesi rejimin özel olarak o crossover'ı
tetiklemek üzere kurgulanmış olmasından. Ayrıca `PerformanceAnalyzer.profit_factor()`
kayıpsız (all-win) pencerelerde `gross_loss==0` olduğu için 0 döndürüyor (sonsuz/çok
yüksek PF yerine) — küçük ama yanıltıcı bir raporlama kusuru, bu 4 maddenin kapsamı
dışında bırakıldı.

`tests/test_backtester_costs.py` (2026-08-11 eklendi) — bkz. "İkinci tur" madde 5.

`tests/test_main_integration.py` (2026-08-11 eklendi, "Üçüncü tur" madde 10)
`tests/test_end_to_end.py`'den FARKLI bir şey test ediyor: o dosya pipeline
bileşenlerini (`DataValidator`/`IndicatorEngine`/`DecisionEngine`/`Backtester`) doğrudan
çağırıyor, gerçek `app.main.main()`'i hiç çalıştırmıyor. Bu dosya `main()`'i sahte
(monkeypatch'li) `BinanceProvider` ile uçtan uca çalıştırıp ağa çıkmadığını, 5 rapor
dosyasının (equity_curve.csv/png, trade_history.csv, drawdown.png, trade_distribution.png)
diskte gerçekten oluştuğunu ve geçersiz veri durumunda erken/temiz çıkıldığını doğruluyor —
main.py'nin dosya I/O ve network tarafını başka hiçbir test kapsamıyordu.

## İkinci tur: çekirdek güçlendirme (2026-08-11)

Yetim modülleri entegre etmeden önce ana pipeline'ı sağlamlaştırma çalışması.

5. ✅ **DÜZELTİLDİ** — `app/broker/fee_model.py` ve `slippage_model.py` MEVCUT ve
   `PaperBroker` -> `ExecutionEngine` üzerinden her trade'de gerçekten çalışıyor (fee
   bakiyeden düşülüyor, slippage giriş/çıkış fiyatına uygulanıyor) — mekanizma baştan
   beri doğruydu. Asıl kırık olan: `Backtester.__init__`, `PaperBroker`'ı `settings.commission`/
   `settings.slippage` GEÇİRMEDEN oluşturuyordu (`PaperBroker(self.portfolio)`), bu yüzden
   `PaperBroker`'ın kendi hardcoded default'ları (0.001 / 0.0005) kullanılıyordu. Ampirik
   kanıt: `settings.commission=0.20` ve `settings.slippage=0.05` yapıp tekrar çalıştırınca
   sonuç BİREBİR AYNI çıktı (10049.99 == 10049.99) — config'in hiçbir etkisi yoktu.
   Fix: `app/backtesting/backtester.py`'de `PaperBroker(self.portfolio, fee_rate=settings.commission,
   slippage=settings.slippage)`. Fix sonrası aynı test: bakiye 10049.99 -> 7243.51 (etkili).
   Regresyonu kilitlemek için `tests/test_backtester_costs.py` eklendi (commission/slippage=0
   ile yüksek değer arasında bakiye farkını doğruluyor). Tüm suite: 154 passed.
6. ✅ **DÜZELTİLDİ** — `BinanceProvider.fetch_ohlcv()`'de hiç try/except yoktu; herhangi bir
   ccxt hatası (rate limit, network timeout, exchange bakımda, yanlış sembol, ...) main.py'ye
   ve `dashboard_data.py`'ye çıplak ccxt exception'ı olarak sızıp programı çökertiyordu.
   `DataValidator.validate()` da sadece `df.empty` ve NaN kontrolü yapıyordu — eksik kolon,
   yetersiz satır sayısı, bozuk OHLC ilişkisi (high<close gibi), negatif fiyat/hacim,
   yinelenen/atlanmış (eksik mum) timestamp'leri hiç yakalamıyordu.
   Fix:
   - `app/data/exceptions.py` -> `DataProviderError` eklendi.
   - `BinanceProvider.fetch_ohlcv()` artık `ccxt.RateLimitExceeded` / `ccxt.NetworkError`
     (= RequestTimeout/ExchangeNotAvailable/DDoSProtection'ı da kapsar) / `ccxt.ExchangeError`
     (= BadSymbol/auth vb.) yakalayıp `logger.error` ile loglayıp `DataProviderError` olarak
     yeniden fırlatıyor (retry/backoff EKLENMEDİ — sadece net hata + graceful exit; retry
     istenirse ayrı bir karar olarak ele alınmalı).
   - `main.py` ve `app/web/dashboard_data.py` artık `DataProviderError`'ı yakalayıp
     (main.py: logla+dön, dashboard: mevcut "N/A" fallback dict'i dön) çöküş yerine
     temiz bir şekilde çıkıyor. NOT: `MultiDataProvider`/`MarketScanner` (yetim modüller)
     bilerek dokunulmadı — artık en azından çıplak ccxt hatası yerine tipli
     `DataProviderError` fırlatıyorlar, ama orada hâlâ yakalanmıyor.
   - `DataValidator.validate()` şimdi sırasıyla kontrol ediyor: eksik kolon, NaN, satır sayısı
     (< `MINIMUM_ROWS=60` — ema_slow=50 + tampon, Ichimoku'nun 78 satırlık cloud warmup'ı
     kasıtlı olarak referans alınmadı çünkü karar zinciri buna bağımlı değil), negatif/sıfır
     fiyat, negatif hacim, `high < max(open,close)` / `low > min(open,close)`, yinelenen
     timestamp, ve medyan mum aralığının >1.5 katı boşluk (eksik mum) — her başarısızlık
     `logger.warning` ile SEBEBİYLE birlikte loglanıyor (öncesinde main.py sadece
     "Invalid market data" diyordu, neden olduğunu söylemiyordu).
   - Yan bulgu: `app/services/market_analyzer.py` diye başka bir yetim modül daha var
     (`app/services/__init__.py` bile yok), `BinanceProvider`+`DataValidator`'ı main.py'den
     bağımsız kullanıyor — round-1 madde 2'deki yetim liste eksikti, buraya not düşüldü.
   Testler: `tests/test_data_validator.py` (11 test, her red sebebi ayrı), `tests/test_binance_provider.py`
   (başarılı fetch + 5 farklı ccxt hata tipinin `DataProviderError`'a sarıldığını doğruluyor).
   Tüm suite: 171 passed.

## Üçüncü tur: paralel geçiş + merge (2026-08-11)

Bu tur, `origin/main`'i hiç `pull` etmemiş AYRI bir local checkout'ta, "İkinci tur"daki
(madde 5-6) 4 maddenin AYNISINI bilmeden bağımsız olarak baştan çözmeye çalışırken ortaya
çıktı. `git push` `! [rejected] (fetch first)` verince fark edildi. `git fetch` + `git merge
origin/main` ile elle çözüldü: madde 5-6'nın (`DataValidator`/`BinanceProvider`/e2e/walk-forward/
cost testleri) origin versiyonu daha kapsamlı olduğu için o taraf kanonik kabul edildi, bu
geçişten SADECE origin'de hiç olmayan gerçek bug fix'leri (madde 7-9) ve tamamlayıcı bir test
(madde 10) korundu. **Ders:** yeni bir oturuma başlamadan `git fetch && git log main..origin/main`
ile local'in origin'in gerisinde olup olmadığı kontrol edilmeli — yoksa aynı işin iki kez
yapılması riski var.

7. ✅ **DÜZELTİLDİ** — çıkışta (sell) slippage `trade.profit`'e hiç yansımıyordu.
   `Backtester.run()` sırası: önce `current_trade.close(exit_price=...)` (kârı bu fiyattan
   hesaplar), sonra `self.broker.close()` -> `ExecutionEngine.execute_sell()`. `execute_sell()`
   `slippage_model.sell_price()` ile `trade.exit_price`'ı güncelliyordu ama `trade.profit`'i
   YENİDEN HESAPLAMIYORDU — gösterilen exit_price ile kullanılan kâr tutarsızdı, çıkış
   slippage'i bakiyeye hiç yansımıyordu (sadece fee yansıyordu). Ampirik kanıt: %1 slippage,
   sıfır fee, giriş 100/çıkış 110 senaryosunda beklenen bakiye 10007.90 iken gerçek sonuç
   10009.00 çıktı (slippage'siz kâr).
   Fix: `Trade.close()`'daki kâr hesaplama `Trade.recalculate_profit()` adlı ayrı bir metoda
   çıkarıldı; `ExecutionEngine.execute_sell()` artık `trade.exit_price`'ı güncelledikten SONRA
   `trade.recalculate_profit()` çağırıyor. `tests/test_execution_engine.py`'e regresyon
   testleri eklendi (fee'nin bakiyeyi tam doğru miktarda düşürdüğünü, slippage'in hem fiyata
   hem kâra doğru yansıdığını sayısal olarak doğruluyor).
8. ✅ **DÜZELTİLDİ** — `TradeDistributionChart.export()` sıfır trade'li bir backtest'te
   çöküyordu. `plt.pie([wins, losses])` wins=losses=0 iken (0/0) matplotlib içinde NaN açı
   üretip `ValueError: cannot convert float NaN to integer` fırlatıyordu — yani main.py hiç
   trade açmayan bir çalıştırmadan sonra rapor aşamasında çöküyordu (madde "İkinci tur"daki
   `test_ema_rsi_walk_forward.py` bulgusu — çoğu pencerede 0 trade — bunun main.py'de tam
   olarak nasıl kırılacağını gösteriyor).
   Fix: wins==0 ve losses==0 olduğunda pasta yerine "No trades" metni çizilip dosyaya
   kaydediliyor. `tests/test_trade_distribution_chart.py`'e regresyon testi eklendi.
9. `BinanceProvider.__init__` artık `ccxt.binance({"enableRateLimit": True})` ile ccxt'nin
   kendi throttling'ini açıyor — madde 6'daki `DataProviderError` yakala-ve-fırlat mekanizmasının
   ÜZERİNE eklendi (rate limit'e hiç çarpmama ihtimalini artırır; çarparsa madde 6 zaten yakalar).
   `tests/test_binance_provider.py`'e `test_provider_enables_rate_limiting` eklendi.
10. `tests/test_main_integration.py` eklendi — bkz. "Test durumu" bölümü.

Tüm suite bu turdan sonra: 178 passed.

## Dördüncü tur: yetim modül entegrasyonu (2026-08-11)

"İkinci tur"/"Üçüncü tur" ana pipeline'ı sağlamlaştırdıktan sonra, "Bilinen sorunlar"
madde 2'de belgelenen 8 yetim klasörden (`voting`, `agents`, `portfolio`, `position`,
`research`, `analytics`, `scheduler`, `optimization`) hangilerinin entegre edilebileceğine
karar verme turu. Önce kodsuz bir PLAN onaylandı (kavramsal gruplama + en az riskliden en
riskliye sıralama + her modül için tam bağlantı noktası + risk analizi), sonra plan
adım adım, her adımdan sonra test çalıştırıp onay alınarak uygulandı.

11. **Adım 1 — Sharpe/Sortino/Calmar/CAGR** (`app/analytics/{sharpe_ratio,sortino_ratio,
    calmar_ratio}.py` -> `PerformanceAnalyzer`). En düşük riskli adım: saf raporlama, karar/trade
    mantığına dokunmuyor. `PerformanceAnalyzer`'a `sharpe_ratio()`/`sortino_ratio()`
    (`balance_history`'den türetilen period-return listesi üzerinden) ve `cagr()`/
    `calmar_ratio()` eklendi. CAGR formülü kullanıcı kararıyla belirlendi:
    `(bitiş_equity / başlangıç_equity) ^ (365 / gün_sayısı) - 1`, gün sayısı ilk trade'in
    `entry_time`'ından son kapanan trade'in `exit_time`'ına kadar (takvim "bugünü" değil,
    çünkü backtest geçmiş bir pencere üzerinde çalışıyor); toplam kayıpta (`end_equity<=0`)
    negatif taban için fraksiyonel üs alma hatasını önlemek üzere -1.0 (%-100) döndürülüyor.
    `app/analytics/profit_factor.py` BİLİNÇLİ OLARAK entegre edilmedi — `PerformanceAnalyzer.profit_factor()`
    zaten var (0/inf davranışı dahil), aynı isimde iki implementasyon istenmedi.
    main.py konsol raporuna 4 satır eklendi. Testler: `tests/test_performance.py`'e 7 yeni
    test (uptrend'de pozitif Sharpe, yetersiz geçmişte 0, downside'sız Sortino=0, CAGR ikiye
    katlama/sıfır-trade/toplam-kayıp, Calmar'ın CAGR+drawdown'ı doğru birleştirdiği).
    Tüm suite: 185 passed.
12. **Adım 2 — research + optimization** (`app/research/{research_engine,report_builder}.py`,
    `app/optimization/walk_forward.py`). `settings.enable_research: bool = False` eklendi;
    `True` ise main.py backtest sonrası `ResearchEngine().run(profits, df)` ->
    `ResearchReportBuilder.build(...)` çalışıp `reports/research_report.json` yazıyor
    (`ResearchEngine.pipeline` alanı `run()` içinde hiç kullanılmıyor — dead field, olduğu
    gibi bırakıldı, davranış değişikliği değil). `WalkForwardAnalyzer` için yeni
    `main.run_walk_forward()` + `python -m app.main --walk-forward` CLI flag'i eklendi —
    `WalkForwardAnalyzer.generate_windows(df)`'in her penceresinde mevcut `Backtester`'ı
    (train ve test için ayrı ayrı) çağırıyor, yeni backtest mantığı icat edilmedi
    (`tests/test_ema_rsi_walk_forward.py`'nin deseni production'a taşındı). `settings.walk_forward_train_size=250`,
    `walk_forward_test_size=100` eklendi. Testler: `tests/test_main_research.py` (varsayılanda
    rapor yazılmadığı, flag açıkken doğru JSON yapısı, sıfır-trade'li piyasada çökmediği),
    `tests/test_main_walk_forward.py` (2 pencere üretip her ikisini de rapor bastığı, gerçek
    borsaya çıkmadığı, yetersiz/geçersiz veri durumunda temiz çıkış). Tüm suite: 192 passed.
13. **Adım 3 — scheduler** (`app/scheduler/scheduler.py`, zaten birbirine bağlı
    `multi_asset_backtester`/`market_scanner`/`multi_data_provider`). Yeni `main.run_scan()`
    + `python -m app.main --scan` CLI flag'i: `Scheduler().run_once()` çağırıp her sembol
    için ham `Decision`'ı tek satır özet olarak basıyor. Kapsam sınırı: `MarketScanner`'ın
    risk sizing/trade açma mantığı YOK, sadece sinyal raporluyor — bu main()'in tek-sembol
    backtest yoluna hiç dokunmuyor, tamamen paralel bir CLI modu. Planın açık noktası
    doğrulandı: `MultiDataProvider.fetch_all()` (`app/data/multi_data_provider.py`) içeride
    `BinanceProvider.fetch_ohlcv()`'i çağırıyor, yani "İkinci tur" madde 6'daki
    ccxt-hata -> `DataProviderError` sarma mekanizmasını olduğu gibi miras alıyor — ayrıca
    bir try/except eklemeye gerek yoktu, sadece `run_scan()` çağrı noktasında main()'deki
    desenle aynı try/except yeterliydi. Testler: `tests/test_main_scan.py`,
    `tests/test_multi_data_provider.py` (açık noktanın kanıtı: `fetch_all()`'ın
    `DataProviderError`'ı olduğu gibi yukarı ilettiğini doğruluyor). Tüm suite: 197 passed.
14. **Adım 4 — voting + analytics (learning_engine/weight_manager)** — planın en riskli/invaziv
    adımı, `DecisionEngine.evaluate()` ve `Backtester.run()`'ın trade-kapama noktalarını
    değiştiriyor. `settings.enable_voting: bool = False` + `settings.voting_strategies`
    (varsayılan: 4 kayıtlı strateji) eklendi. Yeni `DecisionEngine._vote(df)`:
    `voting_strategies`'teki her stratejiyi çalıştırıp `PerformanceDatabase.load()` ->
    `StrategyStats.from_persisted(data)` (YENİ — `app/analytics/strategy_stats.py`'e eklenen
    adapter; `LearningEngine` ham `{"wins":..,"losses":..}` dict'i persist ediyordu,
    `WeightManager.weight()` ise `StrategyStats` nesnesi bekliyordu, ikisi arasında hiç
    çevirici yoktu) -> `WeightManager.weight(stats)` ile ağırlıklandırıp `VotingEngine.vote()`
    ile birleştiriyor. `evaluate()` SADECE `enable_voting=True` VE constructor'a açıkça bir
    `strategy=` verilmemişse voting'e giriyor — açık strateji parametresi her zaman voting'i
    eziyor (test izolasyonu ve "explicit > config" prensibi için). Kullanıcı kararıyla: trade
    kâr/zararı SADECE ağırlıklı çoğunluğu oluşturan (kazanan) tarafa yazılıyor, kaybeden
    taraftaki stratejilere yazılmıyor — `Decision.contributing_strategies` (yeni alan) sadece
    kazanan sinyal yönünde oy veren strateji adlarını taşıyor, bu `Trade.contributing_strategies`
    (yeni alan, trade açılırken kopyalanıyor) üzerinden trade kapanışına kadar taşınıyor;
    `Backtester._register_learning()` (yeni) 3 kapanış noktasının (STOP_LOSS, TAKE_PROFIT,
    SIGNAL) hepsinde bu listedeki stratejilere `LearningEngine.register_trade()` çağırıyor.
    Liste boşsa (voting kapalıyken hep boş) hiçbir şey yapmıyor — `enable_voting=False`
    iken main.py'nin davranışı BİREBİR AYNI kaldı (bunu doğrulamak için tam suite regresyonsuz
    geçti). Testler: `tests/test_decision_engine_voting.py` (varsayılanda/`strategy=` açıkken
    voting'in devre dışı kaldığı, çoklu stratejinin doğru birleştiği, sadece kazanan tarafın
    `contributing_strategies`'e girdiği, geçmiş win-rate'in ağırlık üzerinden 1-1 berabereyi
    gerçekten bozduğu, berabere durumda HOLD+boş liste), `tests/test_learning_engine_integration.py`
    (uçtan uca `Backtester.run()` ile kapanan her trade'in `data/strategy_stats.json`'a
    doğru yazıldığı — izole `tmp_path` ile, `enable_voting=False` iken hiç yazılmadığı).
    Tüm suite: 204 passed.
15. **Adım 5 — `app/portfolio/` + `app/position/`: ERTELENDİ (kullanıcı kararı).** Bkz.
    yukarıdaki "Klasör yapısı" bölümündeki "Tamamen yetim" listesi — gerekçe orada.
    **GÜNCELLEME (Beşinci tur, 2026-08-11):** bu erteleme kararı sonradan kısmen geri
    alındı — `PortfolioManager` gerçekten entegre edildi, `Position` hâlâ yetim. Bkz.
    "Beşinci tur" bölümü.

Tüm suite bu turdan sonra: 204 passed.

## Beşinci tur: çoklu-pozisyon backtester (feature/multi-position-backtester, main'e merge edildi, 2026-08-11)

`Backtester`'ı tek-sembol/tek-trade mimariden çoklu-sembol/çoklu-pozisyona genişleten,
mimari riski en yüksek tur. Önce kodsuz bir PLAN onaylandı (`current_trade` tekilinin
`PortfolioManager` ile nasıl değişeceği, risk katmanının zaten genelleştirilip
genelleştirilmediği, `MultiAssetBacktester` ile çakışma olup olmadığı, main.py entegrasyonu,
adım adım regresyon kontrolü), sonra 3 fazda uygulandı.

16. **Faz A — `current_trade` yerine `PortfolioManager`, davranış DEĞİŞMİYOR.**
    `Backtester.__init__`'e `self.portfolio_manager = PortfolioManager()` eklendi;
    `run()` içindeki tekil `current_trade` değişkeni `self.portfolio_manager.get_position(symbol)`/
    `register_trade()`/`close_trade()` ile değiştirildi — `settings.symbols[0]` sabit tek
    sembolle çalıştığı için bu, `current_trade`'in 1:1 eşdeğeri (dict'te 0-veya-1 anahtar,
    değişkenin None-veya-Trade olmasıyla birebir aynı). Gerçek `Portfolio` (bakiye/equity)
    hiç değişmedi. Bu adımdan sonra 204/204 test BİREBİR AYNI sonuçla geçti — refactor'ün
    davranış-koruyucu olduğu kanıtlandı. Testler: `tests/test_backtester.py`'e 2 yeni test.
    Tüm suite: 206 passed.
17. **Faz B — gerçek çoklu-sembol yeteneği, `settings.enable_multi_position` flag'i
    (varsayılan `False`) arkasında.** ÖNEMLİ BULGU: `RiskManager`/`PositionSizer`/
    `PortfolioRiskManager` hiç tek-pozisyon varsayımıyla yazılmamış — zaten `Portfolio.open_positions`
    (bir LİSTE) üzerinden TOPLAM riski hesaplıyorlardı, sadece bugüne kadar hiç 2+ pozisyonla
    test edilmemişlerdi çünkü `current_trade` döngüsü buna izin vermiyordu. Yani "çoklu
    pozisyonda toplam risk sınırlama" için YENİ kod yazılmadı, mevcut kod ilk kez gerçekten
    çoklu pozisyonla karşılaştı. `Backtester.run(data)` artık `dict[symbol, DataFrame]`
    de kabul ediyor (`_run_multi`) — flag kapalıyken dict verilirse `ValueError` (güvenlik
    kapısı). Her sembolün verisi ÖNCE ham haliyle `DataValidator.validate` edilip (indikatörlerden
    SONRA validate edilseydi NaN-warmup satırları yüzünden her zaman fail ederdi), geçersiz
    sembol `logger.warning` ile atlanıp diğerleriyle devam ediliyor; geçerli semboller
    `_align_timestamps()` ile ortak zaman ekseninin KESİŞİMİNE hizalanıyor, her sembolün kaç
    mum kaybettiği ayrı ayrı `logger.warning` ile loglanıyor (sıfır kayıpta sessiz). Ortak
    döngünün gövdesi (`_step`) tek-sembol ve çoklu-sembol arasında paylaşılıyor, kod tekrarı yok.
    `app/portfolio/risk_limits.py::RiskLimits` bilinçli olarak entegre EDİLMEDİ (`PortfolioRiskManager`
    ile aynı işi yapıyor). Testler: `tests/test_multi_position_backtester.py` (6 test — eşzamanlı
    pozisyon, `max_open_positions`'ın TOPLAM'ı sınırladığı, zaman hizalama loglaması, geçersiz
    sembol atlama). Tüm suite: 212 passed.
18. **Faz C — `python -m app.main --multi-position` CLI modu.** `run_multi_position()`:
    `MultiDataProvider.fetch_all()` ile veri çekip `Backtester().run(market_data)`'i çağırıyor
    (çağrı öncesi `settings.enable_multi_position = True` set ediliyor). Testler:
    `tests/test_main_multi_position.py` (5 test). Tüm suite: 217 passed.

`MultiAssetBacktester`/`MarketScanner` (yukarı bak) ile İSİM ÇAKIŞMASI var ama kod çakışması
YOK — `MultiAssetBacktester` hâlâ gerçek bir backtest yapmıyor (broker/Trade/Portfolio yok,
sadece tek-seferlik `Decision` döndürüyor), bilinçli olarak dokunulmadı.

Tüm suite bu turdan sonra: 217 passed.

## Altıncı tur: canlı veri akışı + paper trading (Faz 1-3 tamamlandı, main'e merge edildi ve feature/live-paper-trading dalı silindi, 2026-08-11)

Roadmap'teki "Paper Trading"i gerçekleştiren, ilk kez UZUN SÜRE ÇALIŞAN gerçek-zamanlı bir
döngü ekleyen tur (önceki tüm modlar tek-seferlik/offline). Önce kodsuz bir PLAN onaylandı;
kod keşfinde kullanıcının "`app/execution/` hâlâ boş" varsayımının YANLIŞ olduğu ortaya
çıktı — `order.py`/`order_book.py` zaten var ve çalışıyor (bkz. yukarı), yeni kod bu klasöre
eklendi. Faz adı adı test edilip onaylanarak ilerliyor.

19. **Faz 1 — canlı veri akışı, SADECE GÖZLEM (hiç trade açmaz).** `app/execution/live_feed.py::LiveFeed`:
    `settings.timeframe`'e göre bir sonraki mum kapanışını hesaplayıp bekliyor
    (+ `settings.live_poll_buffer_seconds` tamponu), `BinanceProvider.fetch_ohlcv`'i çağırıyor.
    **TASARIM NOTU (plan'da yoktu, uygulama sırasında eklendi):** `fetch_closed_candles()`
    REST yanıtının HER ZAMAN SON satırını atıyor — bir REST poll'ün en son mumu hâlâ oluşuyor
    olabilir (henüz kapanmamış), sadece ondan önceki satırlar güvenilir şekilde kapanmış
    sayılıyor. Bu kontrol edilmezse indikatörler/karar tamamlanmamış bir mum üzerinden
    hesaplanabilirdi. Kaçırılan mumlar `fetch_ohlcv`'in her seferinde son `candle_limit`
    mumu baştan çekmesi sayesinde bir sonraki pollde otomatik geri geliyor ("self-healing");
    birden fazla yeni mum sırayla işleniyor, boşluk varsa `logger.warning` ile loglanıyor.
    `app/execution/live_trader.py::LiveTrader`: her yeni mumda `IndicatorEngine` + `DecisionEngine`
    çalışıp karar logluyor, **`Backtester`/`PaperBroker`/`Portfolio` hiç kurmuyor** — yapısal
    olarak trade açamayacağının kanıtı, testte doğrudan doğrulandı. `main.py`: `run_live_paper_trading()`
    + `--live` flag'i. Testler: `tests/test_live_feed.py`, `tests/test_live_trader.py`,
    `tests/test_main_live.py` (18 test) — ayrıca `live_*.py` dosyalarının kaynağında
    `create_order`/`apiKey`/`secret` gibi kelimelerin GEÇMEDİĞİNİ doğrulayan, klasörü glob'la
    tarayan (hardcoded dosya listesi değil) statik bir güvenlik testi. Tüm suite: 235 passed.
20. **Faz 2 — paper trading motoru, `settings.enable_live_paper_trading` (varsayılan `False`)
    arkasında.** `LiveTrader` artık `Backtester._step()`'i İMZASINA DOKUNMADAN yeniden kullanıyor
    (`_ensure_backtester()` ile tembel/cache'li kurulum — aynı örnek tüm pollerde tekrar
    kullanılıyor ki `Portfolio` bakiyesi doğru birikebilsin). Fiyatlama backtest'in "i+1'in açılışı"
    yaklaşımı yerine **gerçek zamanlı `fetch_ticker` fiyatı** kullanıyor (kullanıcı kararı:
    bu turun amacı backtest idealizasyonuyla canlı koşullar arasındaki farkı ölçmek, bayat
    close fiyatı bu farkı gizlerdi) — `BinanceProvider.fetch_ticker(symbol)` eklendi, aynı
    ccxt-hata -> `DataProviderError` deseniyle. `app/execution/live_state_store.py::LiveStateStore`:
    pozisyon/bakiye kalıcılığı, `data/live_state.json`, atomic write (temp dosya + `os.replace`).
    `restore_into()` **Portfolio/PortfolioManager'ı YERİNDE MUTATE EDİYOR, referansı DEĞİŞTİRMİYOR**
    — `PaperBroker` zaten belirli bir `Portfolio` nesnesine referans tutuyor, referansı
    değiştirmek broker'ı sessizce eski/kopuk bir nesneye yazar hale getirirdi. Yan düzeltme
    (kullanıcı kararı): `app/analytics/performance_db.py::PerformanceDatabase.save()` da aynı
    atomic-write desenine geçirildi — `enable_voting=True` ile canlı çalışırken her trade
    kapanışında tekrar tekrar yazılacağı için eksik atomicity artık teorik değil gerçek bir
    bozulma riskiydi. Testler: `tests/test_live_state_store.py` (8 test), `tests/test_live_trader.py`'e
    6 yeni test (aynı Backtester'ın tekrar kullanıldığı, `_step` reuse'unun trade açtığı,
    fiyatın ticker'dan geldiği VE mum kapanışından GELMEDİĞİ — mum close'undan kasıtlı olarak
    500 birim uzak bir ticker fiyatıyla doğrulandı, state'in her mumda kaydedildiği, state'in
    yeniden başlatmada geri yüklendiği), `tests/test_binance_provider.py`'e `fetch_ticker`
    testleri, `tests/test_performance_database.py`'e atomic-write regresyon testi. Güvenlik
    testi genişletildi (kullanıcı isteği): dosya listesi hardcoded DEĞİL, `app/execution/live_*.py`
    glob'u `live_state_store.py`'yi OTOMATİK kapsıyor, ayrıca "en az 3 dosya tarandı" savunma
    kontrolü eklendi (glob'un sessizce boş eşleşmesine karşı). **Ders:** ilk implementasyonda
    `LiveStateStore.FILE` bazı testlerde izole edilmemişti, bu da GERÇEK `data/live_state.json`'a
    yazıp bir SONRAKİ testin o sızıntıyı restore etmesine (ve yanlış pozisyon/fiyatla test
    başarısız olmasına) yol açtı — modül genelinde `autouse` bir `tmp_path` izolasyon fixture'ı
    ekleyerek düzeltildi, sızan dosya silindi. Tüm suite: 256 passed.

21. **Faz 3 — uzun süreli çalışma dayanıklılığı.** `LiveTrader.run_forever()`'ın döngüsü
    artık her iterasyonu (TÜM process'i değil) try/except ile sarıyor: `poll_once()` sırasında
    çıkan HERHANGİ bir `Exception` (`DataProviderError` dahil) `logger.error` ile loglanıp
    `settings.live_error_retry_seconds` (varsayılan 30) kadar beklenip döngü devam ediyor —
    geçici bir ağ hatası artık haftalarca çalışması gereken process'i çökertmiyor. İSTİSNA:
    yeni `app/execution/live_state_store.py::LiveStateCorruptError` bu genel yakalamaya
    KASITLI OLARAK dahil değil — `except LiveStateCorruptError: raise` ile ayrıca yakalanıp
    tekrar fırlatılıyor, döngüyü durduruyor. Gerekçe: bozuk bir state dosyası yeniden
    denemekle düzelmez, sessizce devam etmek paper-trading geçmişini fark edilmeden
    kaybetmek anlamına gelirdi. `LiveStateStore.load()` artık `json.JSONDecodeError`'ı
    yakalayıp net bir mesajla `LiveStateCorruptError` olarak yeniden fırlatıyor.
    `app/logging/logger.py`: düz `logging.FileHandler` yerine `RotatingFileHandler`
    (`settings.log_max_bytes`=5MB, `settings.log_backup_count`=5) — ROOT logger üzerinden
    `logging.basicConfig()` ile DEĞİL, doğrudan `"ProjectAudo"` adlı logger'a `addHandler`
    ile ekleniyor. **Ders:** `logging.basicConfig()` root logger'da halihazırda handler
    varsa SESSİZCE hiçbir şey yapmıyor — pytest'in kendi logging plugin'i test session'ı
    başlarken root logger'a zaten bir handler ekliyor, bu yüzden orijinal `basicConfig()`
    deseni testte HİÇBİR ZAMAN bizim `RotatingFileHandler`'ımızı gerçekten eklemiyordu
    (`test_logger_uses_rotating_file_handler` önce root logger'ı kontrol edecek şekilde
    yazılıp 0 handler bulup FAIL etti, kök nedeni bulunca düzeltildi). `logger.propagate`
    varsayılanında (`True`) bırakıldı — aksi halde mevcut `caplog`-tabanlı testlerin hepsi
    (birçok dosyada) mesajları yakalayamaz olurdu. **Bellek birikimi (4. madde) hakkında
    bulgu — planda varsayılan sorun ORTADA YOKTU:** `LiveFeed` hiç büyüyen bir bellek arabelleği
    tutmuyor — `fetch_closed_candles()` her pollde API'den sınırlı (`candle_limit-1` satır)
    TAZE bir pencere çekiyor, çağrılar arası biriktirmiyor; bu yüzden `LiveFeed`'in bellek
    ayak izi process ne kadar uzun çalışırsa çalışsın SABİT. Gerçekten büyüyen tek durum
    `Backtester.portfolio.trades`/`balance_history` (her trade/kapanışta bir kayıt) — bilinçli
    olarak dokunulmadı (Faz 2'nin "Backtester'a hiç dokunulmadı" sınırını korumak için,
    ayrıca gerçekçi bir paper-trading ufkunda pratik bir bellek sorunu değil, trim etmek
    de zaten performans geçmişini/audit trail'i bozardı). Testler: `tests/test_logger.py`
    (yeni), `tests/test_live_state_store.py`'e 2 (bozuk JSON'da `load()`/`restore_into()`'nun
    `LiveStateCorruptError` fırlattığı), `tests/test_live_trader.py`'e 2 (`run_forever()`'ın
    geçici hatadan sonra kısa bekleyip devam ettiği — `KeyboardInterrupt` ile deterministik
    olarak durdurularak test edildi çünkü `BaseException`, `except Exception` tarafından
    yakalanmıyor; bozuk state'te ASLA yeniden denemeden hemen durduğu). Tüm suite: 261 passed.

Tüm suite bu turdan sonra: 261 passed.

## Bilinen sorunlar

1. ✅ **DÜZELTİLDİ (2026-08-10)** — AI score bazı yollarda her zaman 0 dönüyordu.
   Kök neden: `app/scanner/market_scanner.py`'deki `MarketScanner.scan()`, ham OHLCV
   df'i `IndicatorEngine.calculate_all` hiç çağırmadan doğrudan
   `DecisionEngine.evaluate(df)`'e veriyordu; `ScoreEngine.score` `FEATURE_WEIGHTS`
   anahtarlarını df'de bulamadığı için skor her zaman 0 kalıyordu. Bu yalnızca
   `MarketScanner`/`MultiAssetBacktester` yolunu etkiliyordu — `main.py`, `Backtester`,
   `dashboard_data.py` zaten `IndicatorEngine.calculate_all`'ı çağırdığı için orada
   sorun yoktu (synthetic veriyle doğrulandı: score=61, boş değil).
   Fix: `MarketScanner.scan()` içine her sembol için `df = IndicatorEngine.calculate_all(df)`
   eklendi (diğer tüm çağıranlarla tutarlı hale getirildi). `pytest tests/test_score_engine.py
   tests/test_ai_decision_engine.py tests/test_decision_engine.py tests/test_decision_engine_v2.py
   tests/test_multi_asset_backtester.py` yeşil.
2. ✅ **DÜZELTİLDİ/GÜNCELLENDİ (2026-08-10, sonra "Dördüncü tur"da entegre edildi 2026-08-11)** —
   `app/voting`, `app/agents`, `app/portfolio`, `app/position`, `app/research`, `app/analytics`,
   `app/scheduler`, `app/optimization` başlangıçta main.py'ye hiç bağlı değildi. "Dördüncü tur"da
   plan onaylanıp `voting`+`analytics`(`enable_voting` flag'i), `research`+`optimization`
   (`enable_research` flag'i + `--walk-forward`), `scheduler` (`--scan`) opt-in olarak
   bağlandı — hepsi varsayılan davranışı değiştirmeyecek şekilde flag/CLI arkasında.
   `app/agents`, `app/portfolio`, `app/position` hâlâ tamamen yetim (agents boş; portfolio/position
   bilinçli olarak ertelendi, gerekçe: Backtester tek-sembol/tek-trade mimarisinde, çoklu
   pozisyon desteği ayrı bir proje). Ayrıntılar için yukarıdaki "Klasör yapısı" bölümündeki
   "Opsiyonel/flag ile bağlı" + "Tamamen yetim" listeleri ve "Dördüncü tur" bölümü.
3. ✅ **DÜZELTİLDİ (2026-08-10)** — `requirements.txt`'te `winloop==0.6.3` platform
   koşulu olmadan sabitti; `app/` içinde hiçbir yerden import edilmiyor (muhtemelen
   Windows'ta `pip freeze` ile araya girmiş), ama satırda marker olmadığı için
   Linux/Mac'te `pip install -r requirements.txt` paketi bulamayıp patlıyordu.
   Fix: PEP 508 ortam işareti eklendi — `winloop==0.6.3; sys_platform == "win32"`.
   Böylece Windows'ta hâlâ kurulur (doğrulandı: `pip install --dry-run -r requirements.txt`
   winloop'u "already satisfied" gösterdi, tüm liste hatasız çözüldü), Linux/Mac'te
   pip bu satırı otomatik atlar.
4. ~~`app/decision/decision_engine.py`'de sessiz exception yutma~~ — GÜNCEL KODDA YOK.
   İki `except Exception` bloğu da (satır ~57 market regime, ~89 AI score) zaten
   `logger.warning(...)` çağırıyor, `except: pass` yok. Muhtemelen son commit
   (`84190e2 "Corrections to code"`) bunu zaten düzeltmiş. `git log -- app/decision/decision_engine.py`
   ile teyit edildi.
5. ⚠️ **BİLİNEN SINIRLAMA (belgelendi, düzeltilmedi — 2026-08-11, "Beşinci tur"da eklendi,
   main'e merge edildi)** — `Backtester._run_multi()`/
   `_align_timestamps()` (çoklu-sembol/çoklu-pozisyon backtest) her sembolün indikatörlerini
   kendi TAM/hizalanmamış serisi
   üzerinde hesaplıyor (warmup'ın doğru kalması için — hizalamadan ÖNCE hesaplanmazsa EMA/RSI
   gibi indikatörler yanlış ısınır), SONRA sembolleri ortak zaman ekseninin kesişimine göre
   filtreliyor. Bu sıralama indikatör DEĞERLERİNİ doğru tutuyor ama bir sembol kesişimde
   ORTADAN (uçlardan değil) mum kaybederse, hizalanmış seride ARDIŞIK görünen iki satır
   arasında gerçekte bir zaman boşluğu olabiliyor — `DecisionEngine.evaluate()`'in ardışık-mum
   varsayımıyla çalışan kısımları (ör. EMA crossover tespiti, `MarketRegimeDetector`'ın son
   pencereye bakan hesapları) bu durumda gerçekte olmayan bir "ardışık mum" üzerinden karar
   verebilir. Kasıtlı olarak düzeltilmedi — kapsamı ayrı bir karar (ör. gap'li sembolleri
   tamamen atlamak ya da indikatörleri hizalama SONRASI yeniden hesaplamak, ikincisi warmup'ı
   bozar) gerektiriyor, bu turun kapsamı dışında bırakıldı.
6. ✅ **DÜZELTİLDİ (2026-08-16)** — `SharpeRatio.calculate()`/`SortinoRatio.calculate()`
   sıfır standart sapma/sıfır downside-deviation durumunda (ör. tüm periyotlar kazançlı,
   `test_ema_rsi_walk_forward.py`'deki all-win pencereler) sessizce `0.0` döndürüyordu —
   bu, gerçekten "edge yok/düz" bir sonuçla ayırt edilemiyordu (`profit_factor()`'daki
   madde 2'deki 0/inf sorununa benzer, ayrı bir kod yolu). Fix: sıfır varyans/deviation
   durumunda ortalama getiriye (`mean`/`mean_return - target_return`) bakılıp işaretine göre
   `float("inf")`/`float("-inf")` (Sharpe için ikisi de mümkün, Sortino için sadece `+inf` —
   `downside_returns` boşsa tanım gereği ortalama `target_return`'ün altına inemez) ya da
   gerçekten düz/getirisiz durumda (`mean == 0`) `0.0` dönüyor. `float("inf")` tercih edildi
   (`None` ya da string sentinel değil) çünkü: (1) `main.py`'nin `f"{...:.2f}"` formatlaması
   sorunsuz çalışıyor ("inf" basılıyor), (2) dönüş tipi hâlâ `float` kalıyor, karşılaştırma
   operatörleri (`>0` gibi mevcut testlerde kullanılan) bozulmuyor, (3) `cagr()`'daki
   `-1.0` sentinel deseniyle tutarlı (adlandırılmış float sentinel, None değil). Bu değerlerin
   herhangi bir JSON çıktısına (research_report.json/live_state.json/strategy_stats.json/web
   dashboard API) yazılıp yazılmadığı ayrıca kontrol edildi — hiçbiri Sharpe/Sortino/Calmar/CAGR
   taşımıyor, sadece main.py konsol çıktısında kullanılıyorlar, bu yüzden `json.dump`'ın
   `Infinity` yazması bugün için bir sorun değil (ileride bir JSON çıktısına eklenirse hatırlanmalı).
   `tests/test_sharpe_ratio.py`/`test_sortino_ratio.py`'e sıfır-varyans/sıfır-downside
   birim testleri, `tests/test_performance.py`'deki `test_sortino_ratio_no_downside_returns_zero`
   `test_sortino_ratio_no_downside_returns_infinite` olarak güncellendi + flat-history=0.0
   testleri eklendi. Tüm suite: 269 passed.
