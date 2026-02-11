import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/asset.dart';
import 'stock_detail_screen.dart';
import 'trade_history_screen.dart';
import 'strategy_screen.dart';
import 'login_screen.dart';
import 'package:intl/intl.dart';
import 'dart:async';
import 'package:fl_chart/fl_chart.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
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
  StreamSubscription? _priceSubscription;

  @override
  void initState() {
    super.initState();
    _fetchData();
    _initWebSocket();
  }

  @override
  void dispose() {
    _priceSubscription?.cancel();
    _searchController.dispose();
    super.dispose();
  }

  void _initWebSocket() {
    _priceSubscription = _apiService.getPriceStream().listen((event) {
      if (event != null && event['type'] == 'price_update') {
        final data = event['data'] as Map<String, dynamic>;
        if (mounted) {
          setState(() {
            data.forEach((symbol, val) {
              _livePrices[symbol] = val['price'].toDouble();
            });
          });
        }
      }
    });
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

  void _handleSearch() async {
    final query = _searchController.text.trim();
    if (query.isEmpty) return;
    setState(() => _isSearching = true);
    final result = await _apiService.searchStock(query);
    setState(() => _isSearching = false);
    if (result != null && result['symbol'] != null && mounted) {
      Navigator.of(context).push(MaterialPageRoute(builder: (context) => StockDetailScreen(symbol: result['symbol']))).then((_) => _fetchData());
    }
  }

  // 💡 청산 모드 다이얼로그 (체크리스트 포함)
  void _showLiquidationDialog() {
    if (_portfolio == null || _portfolio!.isEmpty) return;

    List<String> selectedSymbols = _portfolio!.map((e) => e.symbol).toList();

    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setDialogState) {
          return AlertDialog(
            backgroundColor: const Color(0xFF1E293B),
            title: const Text('⚠️ Portfolio Liquidation', style: TextStyle(color: Colors.redAccent, fontWeight: FontWeight.bold)),
            content: SizedBox(
              width: double.maxFinite,
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Text('Select stocks to sell all positions immediately:', style: TextStyle(color: Colors.white70, fontSize: 13)),
                  const SizedBox(height: 16),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      TextButton(
                        onPressed: () => setDialogState(() => selectedSymbols = _portfolio!.map((e) => e.symbol).toList()),
                        child: const Text('Select All'),
                      ),
                      TextButton(
                        onPressed: () => setDialogState(() => selectedSymbols = []),
                        child: const Text('Clear All'),
                      ),
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
                          subtitle: Text('${asset.quantity} shares', style: const TextStyle(color: Colors.grey, fontSize: 12)),
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
              TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
              ElevatedButton(
                style: ElevatedButton.styleFrom(backgroundColor: Colors.redAccent),
                onPressed: selectedSymbols.isEmpty ? null : () async {
                  Navigator.pop(context);
                  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('⏳ Liquidating selected positions...')));
                  await _apiService.liquidatePositions(selectedSymbols);
                  _fetchData();
                },
                child: const Text('Confirm Sell', style: TextStyle(color: Colors.white)),
              ),
            ],
          );
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    bool isAutoEnabled = _userInfo?['is_auto_trading_enabled'] ?? true;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Nasdaq is God'),
        actions: [
          // 💡 자동매매 마스터 스위치
          IconButton(
            icon: Icon(isAutoEnabled ? Icons.play_circle_fill : Icons.pause_circle_filled, 
                 color: isAutoEnabled ? Colors.greenAccent : Colors.orangeAccent),
            tooltip: 'Master Auto-Trading Switch',
            onPressed: () async {
              await _apiService.toggleMasterAutoTrading();
              _fetchData();
            },
          ),
          IconButton(icon: const Icon(Icons.settings_suggest), onPressed: () => Navigator.of(context).push(MaterialPageRoute(builder: (context) => const StrategyScreen()))),
          IconButton(icon: const Icon(Icons.history), onPressed: () => Navigator.of(context).push(MaterialPageRoute(builder: (context) => const TradeHistoryScreen()))),
          IconButton(icon: const Icon(Icons.logout), onPressed: () async { await _apiService.logout(); if (mounted) Navigator.of(context).pushReplacement(MaterialPageRoute(builder: (context) => const LoginScreen())); }),
        ],
      ),
      backgroundColor: const Color(0xFF0F172A),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _fetchData,
              child: SingleChildScrollView(
                physics: const AlwaysScrollableScrollPhysics(),
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _buildHeader(),
                    const SizedBox(height: 20),
                    if (_marketSentiment != null && _marketSentiment!['error'] == null) ...[
                      _buildMarketSentimentCard(),
                      const SizedBox(height: 20),
                    ],
                    _buildSearchBar(),
                    const SizedBox(height: 24),
                    _buildPortfolioSummary(),
                    const SizedBox(height: 24),
                    if (_equityHistory != null && _equityHistory!.isNotEmpty) ...[
                      const Text('Equity Curve', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white70)),
                      const SizedBox(height: 12),
                      _buildEquityChart(),
                      const SizedBox(height: 24),
                    ],
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text('My Portfolio', style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Colors.white)),
                        // 💡 청산 버튼
                        TextButton.icon(
                          onPressed: _showLiquidationDialog,
                          icon: const Icon(Icons.exit_to_app, color: Colors.redAccent, size: 18),
                          label: const Text('Liquidate', style: TextStyle(color: Colors.redAccent, fontWeight: FontWeight.bold)),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    _buildAssetList(),
                  ],
                ),
              ),
            ),
    );
  }

  Widget _buildMarketSentimentCard() {
    final score = _marketSentiment!['score'];
    final sentiment = _marketSentiment!['sentiment'];
    final summary = _marketSentiment!['summary'];
    final keywords = List<String>.from(_marketSentiment!['keywords'] ?? []);
    Color cardColor;
    if (score >= 60) cardColor = Colors.green[900]!; else if (score <= 40) cardColor = Colors.red[900]!; else cardColor = Colors.blueGrey[800]!;
    return Container(width: double.infinity, padding: const EdgeInsets.all(16), decoration: BoxDecoration(gradient: LinearGradient(colors: [cardColor.withOpacity(0.8), cardColor.withOpacity(0.4)]), borderRadius: BorderRadius.circular(16), border: Border.all(color: Colors.white10)), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [const Row(children: [Icon(Icons.psychology, color: Colors.white, size: 24), SizedBox(width: 8), Text('AI Market Briefing', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16))]), Container(padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4), decoration: BoxDecoration(color: Colors.white24, borderRadius: BorderRadius.circular(12)), child: Text('$sentiment ($score/100)', style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)))]), const SizedBox(height: 12), Text(summary, style: const TextStyle(color: Colors.white, fontSize: 14)), if (keywords.isNotEmpty) ...[const SizedBox(height: 12), Wrap(spacing: 8, children: keywords.map((k) => Chip(label: Text('#$k', style: const TextStyle(fontSize: 11, color: Colors.white)), backgroundColor: Colors.black26, padding: EdgeInsets.zero, labelPadding: const EdgeInsets.symmetric(horizontal: 8), visualDensity: VisualDensity.compact)).toList())]]));
  }

  Widget _buildHeader() {
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text('Welcome back,', style: TextStyle(fontSize: 16, color: Colors.grey[400])),
      Text(_userInfo?['username'] ?? 'User', style: const TextStyle(fontSize: 28, fontWeight: FontWeight.bold, color: Colors.white)),
    ]);
  }

  Widget _buildSearchBar() {
    return Container(
      decoration: BoxDecoration(color: Colors.white.withOpacity(0.05), borderRadius: BorderRadius.circular(12), border: Border.all(color: Colors.white10)),
      child: TextField(
        controller: _searchController,
        style: const TextStyle(color: Colors.white),
        decoration: InputDecoration(
          hintText: 'Search Ticker (e.g. TSLA, AAPL)',
          hintStyle: const TextStyle(color: Colors.grey),
          prefixIcon: const Icon(Icons.search, color: Colors.blueAccent),
          suffixIcon: _isSearching ? const SizedBox(width: 20, height: 20, child: Padding(padding: EdgeInsets.all(12), child: CircularProgressIndicator(strokeWidth: 2))) : IconButton(icon: const Icon(Icons.arrow_forward, color: Colors.blueAccent), onPressed: _handleSearch),
          border: InputBorder.none,
          contentPadding: const EdgeInsets.symmetric(vertical: 12),
        ),
        onSubmitted: (_) => _handleSearch(),
      ),
    );
  }

  Widget _buildPortfolioSummary() {
    if (_summary == null) return const SizedBox();
    double totalEquity = (_summary!['total_equity'] ?? 0).toDouble();
    double totalProfit = (_summary!['total_profit'] ?? 0).toDouble();
    double profitRate = (_summary!['total_profit_rate'] ?? 0).toDouble();
    double cash = (_summary!['cash_balance'] ?? 0).toDouble();
    final profitColor = totalProfit >= 0 ? Colors.greenAccent : Colors.redAccent;
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(gradient: LinearGradient(colors: [Colors.blue[700]!, Colors.blue[900]!], begin: Alignment.topLeft, end: Alignment.bottomRight), borderRadius: BorderRadius.circular(16), boxShadow: [BoxShadow(color: Colors.blue.withOpacity(0.2), blurRadius: 10, offset: const Offset(0, 4))]),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        const Text('Total Net Worth (Cash + Stocks)', style: TextStyle(color: Colors.white70, fontSize: 14)),
        Text('\$${NumberFormat('#,##0.00').format(totalEquity)}', style: const TextStyle(color: Colors.white, fontSize: 32, fontWeight: FontWeight.bold)),
        const SizedBox(height: 12),
        Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
          Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            const Text('Total Return', style: TextStyle(color: Colors.white60, fontSize: 12)),
            Text('${totalProfit >= 0 ? "+" : ""}\$${NumberFormat('#,##0.00').format(totalProfit)} (${profitRate.toStringAsFixed(2)}%)', style: TextStyle(color: profitColor, fontSize: 16, fontWeight: FontWeight.bold)),
          ]),
          Column(crossAxisAlignment: CrossAxisAlignment.end, children: [
            const Text('Buying Power (Cash)', style: TextStyle(color: Colors.white60, fontSize: 12)),
            Text('\$${NumberFormat('#,##0.00').format(cash)}', style: const TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold)),
          ]),
        ])
      ]),
    );
  }

  Widget _buildEquityChart() {
    List<FlSpot> spots = [];
    for (int i = 0; i < _equityHistory!.length; i++) { spots.add(FlSpot(i.toDouble(), (_equityHistory![i]['total_equity'] as num).toDouble())); }
    return Container(height: 150, width: double.infinity, padding: const EdgeInsets.symmetric(horizontal: 8), child: LineChart(LineChartData(gridData: const FlGridData(show: false), titlesData: const FlTitlesData(show: false), borderData: FlBorderData(show: false), lineBarsData: [LineChartBarData(spots: spots, isCurved: true, color: Colors.greenAccent, barWidth: 2, dotData: const FlDotData(show: false), belowBarData: BarAreaData(show: true, color: Colors.greenAccent.withOpacity(0.05)))])));
  }

  Widget _buildAssetList() {
    if (_portfolio == null || _portfolio!.isEmpty) {
      return Container(width: double.infinity, padding: const EdgeInsets.symmetric(vertical: 40), decoration: BoxDecoration(color: Colors.white.withOpacity(0.02), borderRadius: BorderRadius.circular(12)), child: const Column(children: [Icon(Icons.pie_chart_outline, size: 48, color: Colors.grey), SizedBox(height: 12), Text('No assets found.', style: TextStyle(color: Colors.grey))]));
    }
    return ListView.separated(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      itemCount: _portfolio!.length,
      separatorBuilder: (context, index) => const Divider(color: Colors.white10, height: 1),
      itemBuilder: (context, index) {
        final asset = _portfolio![index];
        final currentPrice = _livePrices[asset.symbol] ?? asset.currentPrice;
        final profit = (currentPrice - asset.averagePrice) * asset.quantity;
        final profitRate = ((currentPrice / asset.averagePrice) - 1) * 100;
        final assetProfitColor = profit >= 0 ? Colors.greenAccent : Colors.redAccent;
        return ListTile(
          contentPadding: const EdgeInsets.symmetric(vertical: 8),
          title: Row(children: [Text(asset.symbol, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18, color: Colors.white)), const SizedBox(width: 8), Container(padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2), decoration: BoxDecoration(color: assetProfitColor.withOpacity(0.1), borderRadius: BorderRadius.circular(4)), child: Text('${profitRate >= 0 ? "+" : ""}${profitRate.toStringAsFixed(2)}%', style: TextStyle(color: assetProfitColor, fontSize: 12, fontWeight: FontWeight.bold)))]),
          subtitle: Text('${asset.quantity} shares · Avg \$${asset.averagePrice.toStringAsFixed(2)}', style: const TextStyle(color: Colors.grey, fontSize: 13)),
          trailing: Column(mainAxisAlignment: MainAxisAlignment.center, crossAxisAlignment: CrossAxisAlignment.end, children: [Text('\$${NumberFormat('#,##0.00').format(currentPrice * asset.quantity)}', style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.white, fontSize: 16)), Text('${profit >= 0 ? "+" : ""}\$${profit.toStringAsFixed(2)}', style: TextStyle(fontSize: 12, color: assetProfitColor))]),
          onTap: () { Navigator.of(context).push(MaterialPageRoute(builder: (context) => StockDetailScreen(symbol: asset.symbol))).then((_) => _fetchData()); },
        );
      },
    );
  }
}
