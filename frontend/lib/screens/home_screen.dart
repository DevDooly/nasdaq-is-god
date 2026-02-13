import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/asset.dart';
import 'stock_detail_screen.dart';
import 'trade_history_screen.dart';
import 'strategy_screen.dart';
import 'guru_screen.dart';
import 'settings_screen.dart';
import 'login_screen.dart';
import 'package:intl/intl.dart';
import 'dart:async';
import 'package:fl_chart/fl_chart.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> with TickerProviderStateMixin {
  final ApiService _apiService = ApiService();
  final _searchController = TextEditingController();
  Map<String, dynamic>? _userInfo;
  List<StockAsset>? _portfolio;
  Map<String, dynamic>? _summary;
  List<dynamic>? _equityHistory;
  Map<String, dynamic>? _marketSentiment;
  bool _isLoading = true;
  bool _isSearching = false;
  
  Map<String, double> _livePrices = {};
  Map<String, Color> _priceBlinkColors = {};
  StreamSubscription? _updateSubscription;

  @override
  void initState() {
    super.initState();
    _fetchData();
    _initWebSocket();
  }

  @override
  void dispose() {
    _updateSubscription?.cancel();
    _searchController.dispose();
    super.dispose();
  }

  void _initWebSocket() {
    _updateSubscription = _apiService.getUpdateStream().listen((event) {
      if (event == null) return;

      if (event['type'] == 'price_update') {
        final data = event['data'] as Map<String, dynamic>;
        if (mounted) {
          setState(() {
            data.forEach((symbol, val) {
              double newPrice = val['price'].toDouble();
              if (_livePrices.containsKey(symbol) && _livePrices[symbol] != newPrice) {
                _priceBlinkColors[symbol] = newPrice > _livePrices[symbol]! ? Colors.greenAccent : Colors.redAccent;
                Timer(const Duration(milliseconds: 500), () {
                  if (mounted) setState(() => _priceBlinkColors.remove(symbol));
                });
              }
              _livePrices[symbol] = newPrice;
            });
          });
        }
      } else if (event['type'] == 'notification') {
        final data = event['data'] as Map<String, dynamic>;
        _showRealtimeNotification(data['title'], data['body']);
      }
    });
  }

  void _showRealtimeNotification(String title, String body) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Row(
          children: [
            const Icon(Icons.notifications_active, color: Colors.white),
            const SizedBox(width: 12),
            Expanded(child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(title, style: const TextStyle(fontWeight: FontWeight.bold)),
              Text(body, style: const TextStyle(fontSize: 12, color: Colors.white70)),
            ])),
          ],
        ),
        backgroundColor: Colors.blueAccent[700],
        behavior: SnackBarBehavior.floating,
        margin: const EdgeInsets.all(16),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      ),
    );
  }

  Future<void> _fetchData() async {
    setState(() => _isLoading = true);
    final results = await Future.wait([
      _apiService.getMe(),
      _apiService.getPortfolio(),
      _apiService.getPortfolioHistory(),
      _apiService.getMarketSentiment(),
    ]);
    
    if (mounted) {
      setState(() {
        _userInfo = results[0] as Map<String, dynamic>?;
        final portfolioRaw = results[1] as Map<String, dynamic>?;
        if (portfolioRaw != null) {
          final assetsList = portfolioRaw['assets'] as List;
          _portfolio = assetsList.map((item) => StockAsset.fromJson(item)).toList();
          _summary = portfolioRaw['summary'] as Map<String, dynamic>?;
        }
        _equityHistory = results[2] as List<dynamic>?;
        _marketSentiment = results[3] as Map<String, dynamic>?;
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF020617),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: Colors.cyanAccent))
          : Row(
              children: [
                if (MediaQuery.of(context).size.width > 900) _buildSidebar(),
                Expanded(
                  child: RefreshIndicator(
                    onRefresh: _fetchData,
                    color: Colors.cyanAccent,
                    child: CustomScrollView(
                      slivers: [
                        _buildAppBar(),
                        SliverPadding(
                          padding: const EdgeInsets.all(24),
                          sliver: SliverList(
                            delegate: SliverChildListDelegate([
                              _buildTopRow(),
                              const SizedBox(height: 24),
                              _buildMainContent(),
                            ]),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
    );
  }

  Widget _buildSidebar() {
    return Container(
      width: 80,
      color: const Color(0xFF020617),
      child: Column(
        children: [
          const SizedBox(height: 40),
          const Icon(Icons.auto_graph, color: Colors.cyanAccent, size: 32),
          const Spacer(),
          _sidebarIcon(Icons.dashboard, true),
          _sidebarIcon(Icons.psychology, false, onTap: () => Navigator.push(context, MaterialPageRoute(builder: (context) => const GuruScreen()))),
          _sidebarIcon(Icons.settings_suggest, false, onTap: () => Navigator.push(context, MaterialPageRoute(builder: (context) => const StrategyScreen()))),
          _sidebarIcon(Icons.history, false, onTap: () => Navigator.push(context, MaterialPageRoute(builder: (context) => const TradeHistoryScreen()))),
          _sidebarIcon(Icons.settings, false, onTap: () => Navigator.push(context, MaterialPageRoute(builder: (context) => const SettingsScreen()))),
          const Spacer(),
          _sidebarIcon(Icons.logout, false, onTap: () async {
            await _apiService.logout();
            if (mounted) Navigator.pushReplacement(context, MaterialPageRoute(builder: (context) => const LoginScreen()));
          }),
          const SizedBox(height: 20),
        ],
      ),
    );
  }

  Widget _sidebarIcon(IconData icon, bool active, {VoidCallback? onTap}) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 16),
      child: InkWell(
        onTap: onTap,
        child: Icon(icon, color: active ? Colors.cyanAccent : Colors.grey[600], size: 28),
      ),
    );
  }

  Widget _buildAppBar() {
    bool isAutoEnabled = _userInfo?['is_auto_trading_enabled'] ?? true;
    return SliverAppBar(
      floating: true,
      pinned: true,
      backgroundColor: const Color(0xFF020617).withOpacity(0.8),
      title: Row(
        children: [
          Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('터미널', style: TextStyle(fontSize: 12, color: Colors.cyanAccent.withOpacity(0.7), letterSpacing: 2)),
            Text('나스닥의 신', style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 22)),
          ]),
          const SizedBox(width: 16),
          _buildLiveIndicator(),
        ],
      ),
      actions: [
        IconButton(
          icon: const Icon(Icons.search),
          onPressed: _showSearchDialog,
        ),
        IconButton(
          icon: Icon(isAutoEnabled ? Icons.play_circle_fill : Icons.pause_circle_filled, 
               color: isAutoEnabled ? Colors.greenAccent : Colors.orangeAccent, size: 28),
          onPressed: () async {
            await _apiService.toggleMasterAutoTrading();
            _fetchData();
          },
        ),
        if (MediaQuery.of(context).size.width <= 900) ...[
          IconButton(icon: const Icon(Icons.psychology, color: Colors.purpleAccent), onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (context) => const GuruScreen()))),
          IconButton(icon: const Icon(Icons.settings), onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (context) => const SettingsScreen()))),
          IconButton(icon: const Icon(Icons.logout), onPressed: () async {
            await _apiService.logout();
            Navigator.pushReplacement(context, MaterialPageRoute(builder: (context) => const LoginScreen()));
          }),
        ],
        const SizedBox(width: 12),
      ],
    );
  }

  void _showSearchDialog() {
    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setDialogState) {
          return AlertDialog(
            backgroundColor: const Color(0xFF1E293B),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
            title: const Text('종목 검색', style: TextStyle(color: Colors.cyanAccent, fontSize: 14, fontWeight: FontWeight.bold, letterSpacing: 2)),
            content: TextField(
              controller: _searchController,
              autofocus: true,
              style: const TextStyle(color: Colors.white, fontFamily: 'monospace'),
              decoration: InputDecoration(
                hintText: '티커 또는 종목명 입력 (예: TSLA)',
                hintStyle: TextStyle(color: Colors.white.withOpacity(0.3)),
                prefixIcon: const Icon(Icons.search, color: Colors.cyanAccent),
                filled: true,
                fillColor: Colors.white.withOpacity(0.05),
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
              ),
              onSubmitted: (val) async {
                if (val.isEmpty) return;
                setDialogState(() => _isSearching = true);
                final result = await _apiService.searchStock(val);
                setDialogState(() => _isSearching = false);
                if (result != null && mounted) {
                  Navigator.pop(context);
                  Navigator.push(context, MaterialPageRoute(builder: (context) => StockDetailScreen(symbol: result['symbol'])));
                } else if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('종목을 찾을 수 없습니다.')));
                }
              },
            ),
            actions: [
              TextButton(onPressed: () => Navigator.pop(context), child: const Text('취소')),
              if (_isSearching)
                const Padding(
                  padding: EdgeInsets.symmetric(horizontal: 16),
                  child: SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.cyanAccent)),
                )
              else
                ElevatedButton(
                  onPressed: () async {
                    if (_searchController.text.isEmpty) return;
                    setDialogState(() => _isSearching = true);
                    final result = await _apiService.searchStock(_searchController.text);
                    setDialogState(() => _isSearching = false);
                    if (result != null && mounted) {
                      Navigator.pop(context);
                      Navigator.push(context, MaterialPageRoute(builder: (context) => StockDetailScreen(symbol: result['symbol'])));
                    } else if (mounted) {
                      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('종목을 찾을 수 없습니다.')));
                    }
                  },
                  style: ElevatedButton.styleFrom(backgroundColor: Colors.cyanAccent[700]),
                  child: const Text('검색'),
                ),
            ],
          );
        },
      ),
    );
  }

  Widget _buildLiveIndicator() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(color: Colors.greenAccent.withOpacity(0.1), borderRadius: BorderRadius.circular(20), border: Border.all(color: Colors.greenAccent.withOpacity(0.3))),
      child: Row(children: [
        Container(width: 6, height: 6, decoration: const BoxDecoration(color: Colors.greenAccent, shape: BoxShape.circle)),
        const SizedBox(width: 6),
        const Text('실시간', style: TextStyle(color: Colors.greenAccent, fontSize: 10, fontWeight: FontWeight.bold)),
      ]),
    );
  }

  Widget _buildTopRow() {
    return LayoutBuilder(builder: (context, constraints) {
      if (constraints.maxWidth > 800) {
        return Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(flex: 3, child: _buildPortfolioSummary()),
            const SizedBox(width: 24),
            Expanded(flex: 2, child: _buildMarketSentimentCard()),
          ],
        );
      } else {
        return Column(children: [
          _buildPortfolioSummary(),
          const SizedBox(height: 24),
          _buildMarketSentimentCard(),
        ]);
      }
    });
  }

  Widget _buildPortfolioSummary() {
    if (_summary == null) return const SizedBox();
    double totalEquity = (_summary!['total_equity'] ?? 0).toDouble();
    double totalProfit = (_summary!['total_profit'] ?? 0).toDouble();
    double profitRate = (_summary!['total_profit_rate'] ?? 0).toDouble();
    final profitColor = totalProfit >= 0 ? Colors.greenAccent : Colors.redAccent;

    return Container(
      padding: const EdgeInsets.all(24),
      decoration: _glassDecoration(),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text('총 자산 가치', style: TextStyle(color: Colors.cyanAccent.withOpacity(0.5), fontSize: 12, letterSpacing: 1)),
        const SizedBox(height: 8),
        Row(crossAxisAlignment: CrossAxisAlignment.end, children: [
          Text('\$${NumberFormat('#,##0.00').format(totalEquity)}', style: const TextStyle(fontSize: 36, fontWeight: FontWeight.bold, color: Colors.white)),
          const SizedBox(width: 12),
          Padding(
            padding: const EdgeInsets.only(bottom: 6),
            child: Text('${totalProfit >= 0 ? "+" : ""}${profitRate.toStringAsFixed(2)}%', style: TextStyle(color: profitColor, fontWeight: FontWeight.bold, fontSize: 18)),
          ),
        ]),
        const SizedBox(height: 24),
        Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
          _summaryItem('매수 가능 금액', '\$${NumberFormat('#,##0.00').format(_summary!['cash_balance'])}'),
          _summaryItem('미실현 손익', '\$${NumberFormat('#,##0.00').format(totalProfit)}', color: profitColor),
        ]),
      ]),
    );
  }

  Widget _summaryItem(String label, String value, {Color? color}) {
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text(label, style: const TextStyle(color: Colors.grey, fontSize: 12)),
      Text(value, style: TextStyle(color: color ?? Colors.white, fontSize: 16, fontWeight: FontWeight.bold, fontFamily: 'monospace')),
    ]);
  }

  Widget _buildMarketSentimentCard() {
    if (_marketSentiment == null) return const SizedBox();
    if (_marketSentiment!['error'] != null) {
      return Container(padding: const EdgeInsets.all(24), decoration: _glassDecoration(), child: const Center(child: Text('AI 분석 오프라인', style: TextStyle(color: Colors.grey))));
    }
    final score = _marketSentiment!['score'] ?? 50;
    final sentiment = _marketSentiment!['sentiment'] ?? 'Neutral';
    final summary = _marketSentiment!['summary'] ?? '';
    
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: _glassDecoration(color: Colors.purpleAccent.withOpacity(0.05)),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
          const Text('시장 상태', style: TextStyle(color: Colors.purpleAccent, fontSize: 12, letterSpacing: 1, fontWeight: FontWeight.bold)),
          Text('$score/100', style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
        ]),
        const SizedBox(height: 16),
        Text(sentiment.toUpperCase() == 'BULLISH' ? '강세' : (sentiment.toUpperCase() == 'BEARISH' ? '약세' : '중립'), 
            style: TextStyle(color: score >= 50 ? Colors.greenAccent : Colors.redAccent, fontSize: 24, fontWeight: FontWeight.w900)),
        const SizedBox(height: 8),
        Text(summary, maxLines: 2, overflow: TextOverflow.ellipsis, style: const TextStyle(color: Colors.white70, fontSize: 13)),
      ]),
    );
  }

  Widget _buildMainContent() {
    return LayoutBuilder(builder: (context, constraints) {
      if (constraints.maxWidth > 1000) {
        return Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Expanded(flex: 3, child: _buildAssetSection()),
          const SizedBox(width: 24),
          Expanded(flex: 2, child: _buildEquityCurveSection()),
        ]);
      } else {
        return Column(children: [
          _buildEquityCurveSection(),
          const SizedBox(height: 24),
          _buildAssetSection(),
        ]);
      }
    });
  }

  Widget _buildAssetSection() {
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
        const Text('포트폴리오 현황', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        TextButton.icon(onPressed: _showLiquidationDialog, icon: const Icon(Icons.bolt, color: Colors.redAccent), label: const Text('전량 매도', style: TextStyle(color: Colors.redAccent, fontWeight: FontWeight.bold))),
      ]),
      const SizedBox(height: 16),
      _buildAssetList(),
    ]);
  }

  Widget _buildEquityCurveSection() {
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      const Text('자산 변동 추이', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
      const SizedBox(height: 16),
      Container(padding: const EdgeInsets.all(20), decoration: _glassDecoration(), child: _buildEquityChart()),
    ]);
  }

  Widget _buildAssetList() {
    if (_portfolio == null || _portfolio!.isEmpty) return const Center(child: Padding(padding: EdgeInsets.all(40), child: Text('포트폴리오가 비어 있습니다')));
    return ListView.separated(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      itemCount: _portfolio!.length,
      separatorBuilder: (context, index) => const SizedBox(height: 12),
      itemBuilder: (context, index) {
        final asset = _portfolio![index];
        final curPrice = _livePrices[asset.symbol] ?? asset.currentPrice;
        final blinkColor = _priceBlinkColors[asset.symbol];
        final profitRate = ((curPrice / asset.averagePrice) - 1) * 100;

        return InkWell(
          onTap: () => Navigator.push(context, MaterialPageRoute(builder: (context) => StockDetailScreen(symbol: asset.symbol))).then((_) => _fetchData()),
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 300),
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
            decoration: _glassDecoration(color: blinkColor?.withOpacity(0.1)),
            child: Row(children: [
              Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(asset.symbol, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                Text('${asset.quantity} 주', style: const TextStyle(color: Colors.grey, fontSize: 12)),
              ]),
              const Spacer(),
              _buildPriceColumn(curPrice, profitRate, blinkColor),
            ]),
          ),
        );
      },
    );
  }

  Widget _buildPriceColumn(double price, double rate, Color? blink) {
    return Column(crossAxisAlignment: CrossAxisAlignment.end, children: [
      Text('\$${price.toStringAsFixed(2)}', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: blink ?? Colors.white, fontFamily: 'monospace')),
      Text('${rate >= 0 ? "+" : ""}${rate.toStringAsFixed(2)}%', style: TextStyle(color: rate >= 0 ? Colors.greenAccent : Colors.redAccent, fontSize: 12, fontWeight: FontWeight.bold)),
    ]);
  }

  Widget _buildEquityChart() {
    if (_equityHistory == null || _equityHistory!.isEmpty) return const SizedBox(height: 200, child: Center(child: Text('데이터 없음')));
    List<FlSpot> spots = [];
    for (int i = 0; i < _equityHistory!.length; i++) {
      spots.add(FlSpot(i.toDouble(), (_equityHistory![i]['total_equity'] as num).toDouble()));
    }
    return SizedBox(
      height: 250,
      child: LineChart(LineChartData(
        lineTouchData: LineTouchData(
          touchTooltipData: LineTouchTooltipData(
            tooltipBgColor: const Color(0xFF1E293B),
            getTooltipItems: (List<LineBarSpot> touchedSpots) {
              return touchedSpots.map((LineBarSpot touchedSpot) {
                return LineTooltipItem(
                  '\$${NumberFormat('#,##0').format(touchedSpot.y)}',
                  const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                );
              }).toList();
            },
          ),
        ),
        gridData: FlGridData(
          show: true,
          drawVerticalLine: true,
          horizontalInterval: 10000,
          verticalInterval: 1,
          getDrawingHorizontalLine: (value) => FlLine(color: Colors.white.withOpacity(0.05), strokeWidth: 1),
          getDrawingVerticalLine: (value) => FlLine(color: Colors.white.withOpacity(0.05), strokeWidth: 1),
        ),
        titlesData: FlTitlesData(
          show: true,
          bottomTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              reservedSize: 30,
              interval: (_equityHistory!.length / 5).clamp(1, double.infinity),
              getTitlesWidget: (value, meta) {
                int index = value.toInt();
                if (index < 0 || index >= _equityHistory!.length) return const SizedBox();
                DateTime date = DateTime.parse(_equityHistory![index]['timestamp']).toLocal();
                return Padding(
                  padding: const EdgeInsets.only(top: 8.0),
                  child: Text(DateFormat('MM/dd').format(date), style: TextStyle(color: Colors.grey[600], fontSize: 10)),
                );
              },
            ),
          ),
          leftTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              reservedSize: 60,
              getTitlesWidget: (value, meta) {
                return SideTitleWidget(
                  axisSide: meta.axisSide,
                  child: Text(
                    NumberFormat('#,###').format(value),
                    style: TextStyle(color: Colors.grey[600], fontSize: 10),
                  ),
                );
              },
            ),
          ),
          topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
        ),
        borderData: FlBorderData(show: false),
        lineBarsData: [
          LineChartBarData(
            spots: spots,
            isCurved: true,
            color: Colors.cyanAccent,
            barWidth: 3,
            isStrokeCapRound: true,
            dotData: const FlDotData(show: false),
            belowBarData: BarAreaData(show: true, gradient: LinearGradient(colors: [Colors.cyanAccent.withOpacity(0.2), Colors.cyanAccent.withOpacity(0)], begin: Alignment.topCenter, end: Alignment.bottomCenter)),
          ),
        ],
      )),
    );
  }

  void _showLiquidationDialog() {
    if (_portfolio == null || _portfolio!.isEmpty) return;
    List<String> selectedSymbols = _portfolio!.map((e) => e.symbol).toList();
    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setDialogState) {
          return AlertDialog(
            backgroundColor: const Color(0xFF1E293B),
            title: const Text('⚠️ 포트폴리오 전량 매도', style: TextStyle(color: Colors.redAccent, fontWeight: FontWeight.bold)),
            content: SizedBox(
              width: double.maxFinite,
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Text('즉시 매도할 종목을 선택하세요:', style: TextStyle(color: Colors.white70, fontSize: 13)),
                  const SizedBox(height: 16),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      TextButton(onPressed: () => setDialogState(() => selectedSymbols = _portfolio!.map((e) => e.symbol).toList()), child: const Text('전체 선택')),
                      TextButton(onPressed: () => setDialogState(() => selectedSymbols = []), child: const Text('전체 해제')),
                    ],
                  ),
                  const Divider(color: Colors.white10),
                  Flexible(
                    child: ListView.builder(
                      shrinkWrap: true,
                      itemCount: _portfolio!.length,
                      itemBuilder: (context, index) {
                        final asset = _portfolio![index];
                        return CheckboxListTile(
                          title: Text(asset.symbol, style: const TextStyle(color: Colors.white)),
                          subtitle: Text('${asset.quantity} 주', style: const TextStyle(color: Colors.grey, fontSize: 12)),
                          value: selectedSymbols.contains(asset.symbol),
                          onChanged: (val) {
                            setDialogState(() {
                              if (val == true) selectedSymbols.add(asset.symbol);
                              else selectedSymbols.remove(asset.symbol);
                            });
                          },
                        );
                      },
                    ),
                  ),
                ],
              ),
            ),
            actions: [
              TextButton(onPressed: () => Navigator.pop(context), child: const Text('취소')),
              ElevatedButton(
                style: ElevatedButton.styleFrom(backgroundColor: Colors.redAccent),
                onPressed: selectedSymbols.isEmpty ? null : () async {
                  Navigator.pop(context);
                  await _apiService.liquidatePositions(selectedSymbols);
                  _fetchData();
                },
                child: const Text('매수 확정', style: TextStyle(color: Colors.white)),
              ),
            ],
          );
        },
      ),
    );
  }

  BoxDecoration _glassDecoration({Color? color}) {
    return BoxDecoration(
      color: color ?? Colors.white.withOpacity(0.03),
      borderRadius: BorderRadius.circular(16),
      border: Border.all(color: Colors.white.withOpacity(0.08)),
      boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.2), blurRadius: 10, offset: const Offset(0, 4))],
    );
  }
}
