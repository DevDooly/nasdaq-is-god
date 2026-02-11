import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/asset.dart';
import 'stock_detail_screen.dart';
import 'trade_history_screen.dart';
import 'strategy_screen.dart';
import 'login_screen.dart';
import 'package:intl/intl.dart';
import 'dart:async';

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
    final user = await _apiService.getMe();
    final dynamic portfolioRaw = await _apiService.getPortfolio();
    
    if (mounted) {
      setState(() {
        _userInfo = user;
        if (portfolioRaw != null && portfolioRaw is Map<String, dynamic>) {
          final assetsList = portfolioRaw['assets'] as List;
          _portfolio = assetsList.map((item) => StockAsset.fromJson(item)).toList();
          _summary = portfolioRaw['summary'] as Map<String, dynamic>?;
        }
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

    if (result != null && result['symbol'] != null) {
      if (mounted) {
        Navigator.of(context).push(
          MaterialPageRoute(
            builder: (context) => StockDetailScreen(symbol: result['symbol']),
          ),
        ).then((_) => _fetchData());
      }
    } else {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('종목을 찾을 수 없습니다.')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Nasdaq is God'),
        actions: [
          IconButton(
            icon: const Icon(Icons.settings_suggest),
            onPressed: () => Navigator.of(context).push(
              MaterialPageRoute(builder: (context) => const StrategyScreen()),
            ),
          ),
          IconButton(
            icon: const Icon(Icons.history),
            onPressed: () => Navigator.of(context).push(
              MaterialPageRoute(builder: (context) => const TradeHistoryScreen()),
            ),
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _fetchData,
          ),
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () async {
              await _apiService.logout();
              if (mounted) {
                Navigator.of(context).pushReplacement(
                  MaterialPageRoute(builder: (context) => const LoginScreen()),
                );
              }
            },
          ),
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
                    _buildSearchBar(),
                    const SizedBox(height: 24),
                    _buildPortfolioSummary(),
                    const SizedBox(height: 24),
                    const Text(
                      'My Portfolio',
                      style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Colors.white),
                    ),
                    const SizedBox(height: 12),
                    _buildAssetList(),
                  ],
                ),
              ),
            ),
    );
  }

  Widget _buildHeader() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('Welcome back,', style: TextStyle(fontSize: 16, color: Colors.grey[400])),
        Text(_userInfo?['username'] ?? 'User', style: const TextStyle(fontSize: 28, fontWeight: FontWeight.bold, color: Colors.white)),
      ],
    );
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
      decoration: BoxDecoration(
        gradient: LinearGradient(colors: [Colors.blue[700]!, Colors.blue[900]!], begin: Alignment.topLeft, end: Alignment.bottomRight),
        borderRadius: BorderRadius.circular(16),
        boxShadow: [BoxShadow(color: Colors.blue.withOpacity(0.2), blurRadius: 10, offset: const Offset(0, 4))],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Total Net Worth (Cash + Stocks)', style: TextStyle(color: Colors.white70, fontSize: 14)),
          Text('\$${NumberFormat('#,##0.00').format(totalEquity)}', style: const TextStyle(color: Colors.white, fontSize: 32, fontWeight: FontWeight.bold)),
          const SizedBox(height: 12),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Total Return', style: TextStyle(color: Colors.white60, fontSize: 12)),
                  Text(
                    '${totalProfit >= 0 ? "+" : ""}\$${NumberFormat('#,##0.00').format(totalProfit)} (${profitRate.toStringAsFixed(2)}%)',
                    style: TextStyle(color: profitColor, fontSize: 16, fontWeight: FontWeight.bold),
                  ),
                ],
              ),
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  const Text('Buying Power (Cash)', style: TextStyle(color: Colors.white60, fontSize: 12)),
                  Text('\$${NumberFormat('#,##0.00').format(cash)}', style: const TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold)),
                ],
              ),
            ],
          )
        ],
      ),
    );
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
          title: Row(
            children: [
              Text(asset.symbol, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18, color: Colors.white)),
              const SizedBox(width: 8),
              Container(padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2), decoration: BoxDecoration(color: assetProfitColor.withOpacity(0.1), borderRadius: BorderRadius.circular(4)), child: Text('${profitRate >= 0 ? "+" : ""}${profitRate.toStringAsFixed(2)}%', style: TextStyle(color: assetProfitColor, fontSize: 12, fontWeight: FontWeight.bold)))
            ],
          ),
          subtitle: Text('${asset.quantity} shares · Avg \$${asset.averagePrice.toStringAsFixed(2)}', style: const TextStyle(color: Colors.grey, fontSize: 13)),
          trailing: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text('\$${NumberFormat('#,##0.00').format(currentPrice * asset.quantity)}', style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.white, fontSize: 16)),
              Text('${profit >= 0 ? "+" : ""}\$${profit.toStringAsFixed(2)}', style: TextStyle(fontSize: 12, color: assetProfitColor)),
            ],
          ),
          onTap: () {
            Navigator.of(context).push(MaterialPageRoute(builder: (context) => StockDetailScreen(symbol: asset.symbol))).then((_) => _fetchData());
          },
        );
      },
    );
  }
}