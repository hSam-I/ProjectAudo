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
       -> SignalScorer.score(df)            ("legacy" kural tabanlı skor)
       -> ScoreEngine.score(df)             (AI feature skoru, app/ai/score_engine.py)
       -> SignalFilter.filter(raw_signal, score)
  -> RiskManager (stop_loss / take_profit / risk_amount)
  -> Backtester().run(df)                   (app/backtesting/backtester.py, kendi içinde
                                              IndicatorEngine.calculate_all'ı TEKRAR çağırır)
  -> PerformanceAnalyzer
  -> TradeJournal / EquityReport / EquityChart / DrawdownChart / TradeDistributionChart
```

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
  `backtest_runner.py`, `performance_report.py` kullanılmıyor.
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
- `execution/` — `order.py`, `order_book.py` (kullanılmıyor)

**Tamamen yetim (main.py'den hiçbir zincirle ulaşılamıyor, sadece kendi testleri var):**
Bu 8 klasör canlı koddan hiçbir yerden import edilmiyor (`grep -rn "app\.<klasör>" app` ile
teyit edildi, sadece birbirlerine referans veriyorlar). Bilinçli olarak dokunulmadı — sadece
belgeleniyor, entegre/silinmedi (2026-08-10 karar).

- `app/voting/` — `VotingEngine.vote(votes)`: birden fazla stratejinin ağırlıklı
  oylarını (Signal + weight) tek bir Signal'e indirger. `DecisionEngine` şu an tek
  strateji kullanıyor, çoklu strateji oylaması yok.
- `app/agents/` — neredeyse boş, sadece `__init__.py` var, hiç sınıf yok. README'deki
  "Multi-Agent Analysis" vizyonunun henüz yazılmamış iskeleti.
- `app/portfolio/` — `PortfolioManager`: symbol->Trade dict'i ile açık pozisyonları
  takip eder (can_open_trade/register_trade/close_trade/total_exposure).
  `app/backtesting/portfolio.py`'deki (gerçekten kullanılan) `Portfolio` sınıfıyla
  KARIŞTIRMA — isim çakışması var ama ayrı, ilgisiz sınıflar. Ayrıca `risk_analyzer.py`,
  `risk_limits.py`, `statistics.py`, `performance_tracker.py` da burada, hepsi yetim.
- `app/position/` — sadece `Position` dataclass'ı (symbol/side/entry_price/quantity).
  Gerçek pozisyon takibi `app/backtesting/trade.py::Trade` ile yapılıyor, bu ayrı/kullanılmayan bir model.
- `app/research/` — `ResearchEngine`: Monte Carlo simülasyonu + risk-of-ruin +
  senaryo çalıştırıcıyı birleştirip rapor üretir. `app/optimization/`'a bağımlı (tek
  gerçek bağlantı bu iki yetim klasör arası).
- `app/analytics/` — `LearningEngine.register_trade()` (strateji win/loss'unu
  `PerformanceDatabase`'e yazar) + `WeightManager.weight()` (win-rate'e göre voting
  ağırlığı hesaplar) + Sharpe/Sortino/Calmar/Drawdown/ProfitFactor hesaplayıcıları.
  Kavramsal olarak `app/voting/` + `app/backtesting/performance.py` ile örtüşüyor ama
  bağlı değil — trade sonrası feedback-loop (strateji ağırlıklarını geçmiş performansa
  göre güncelleme) hiç çalışmıyor.
- `app/scheduler/` — `Scheduler.run_once()` sadece `MultiAssetBacktester().scan()`'ı
  çağırıyor; periyodik/canlı çalıştırma iskeleti ama kendisi de hiçbir yerden
  tetiklenmiyor (cron/loop yok).
- `app/optimization/` — grid search, walk-forward, Monte Carlo, stress test,
  risk-of-ruin gibi strateji parametre optimizasyonu araçları. Sadece
  `app/research/research_engine.py` içeriden kullanıyor; o da yetim.
  NOT: `WalkForwardAnalyzer` (sadece rolling train/test pencere üretiyor, backtest
  mantığı içermiyor) "İkinci tur" madde 2'de test yardımcı aracı olarak kullanıldı —
  bu, main.py pipeline'ına entegre etmek değil, sadece pencere üretme yardımcı sınıfını
  test kodunda ödünç almak (`tests/test_walk_forward.py` zaten aynı şekilde kullanıyordu).
- `app/services/market_analyzer.py` — round-1 taramasında kaçırılmış ekstra bir yetim
  modül (2026-08-11'de fark edildi). `app/services/__init__.py` bile yok. `MarketAnalyzer.analyze()`
  main.py'den bağımsız kendi `BinanceProvider`+`DataValidator`+`EMARSIStrategy`+`SignalScorer`+`RiskManager`
  zincirini kuruyor, hiçbir yerden çağrılmıyor.

Özet: `voting` + `analytics` (weight_manager) birlikte "geçmiş performansa göre
strateji ağırlıklandırma" özelliğini oluşturuyor; `research` + `optimization` birlikte
"parametre optimizasyonu / senaryo analizi" özelliğini oluşturuyor. İkisi de tasarlanmış
ama DecisionEngine/Backtester pipeline'ına hiç kablolanmamış.

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
2. ✅ **BELGELENDİ (2026-08-10)** — `app/voting`, `app/agents`, `app/portfolio`,
   `app/position`, `app/research`, `app/analytics`, `app/scheduler`, `app/optimization`
   main.py'ye bağlı değil. Kullanıcı kararıyla koda dokunulmadı (entegre edilmedi,
   silinmedi) — yukarıdaki "Tamamen yetim" bölümünde her klasörün ne yaptığı ve neden
   yetim olduğu ayrıntılı yazıldı, ileride entegrasyon/silme kararı verilirse oradan
   devam edilebilir.
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
