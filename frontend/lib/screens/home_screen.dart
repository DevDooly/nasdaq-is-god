import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/asset.dart';
import 'stock_detail_screen.dart';
import 'package:intl/intl.dart';

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
  bool _isLoading = true;
  bool _isSearching = false;

  @override
  void initState() {
    super.initState();
    _fetchData();
  }

  Future<void> _fetchData() async {
    setState(() => _isLoading = true);
    final user = await _apiService.getMe();
    final portfolioData = await _apiService.getPortfolio();
    
    if (mounted) {
      setState(() {
        _userInfo = user;
        _portfolio = portfolioData?.map((item) => StockAsset.fromJson(item)).toList();
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
        );
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
            icon: const Icon(Icons.refresh),
            onPressed: _fetchData,
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
        Text(
          'Welcome back,',
          style: TextStyle(fontSize: 16, color: Colors.grey[400]),
        ),
        Text(
          _userInfo?['username'] ?? 'User',
          style: const TextStyle(fontSize: 28, fontWeight: FontWeight.bold, color: Colors.white),
        ),
      ],
    );
  }

  Widget _buildSearchBar() {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.05),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.white10),
      ),
      child: TextField(
        controller: _searchController,
        style: const TextStyle(color: Colors.white),
        decoration: InputDecoration(
          hintText: 'Search Ticker (e.g. TSLA, AAPL)',
          hintStyle: const TextStyle(color: Colors.grey),
          prefixIcon: const Icon(Icons.search, color: Colors.blueAccent),
          suffixIcon: _isSearching 
            ? const SizedBox(width: 20, height: 20, child: Padding(padding: EdgeInsets.all(12), child: CircularProgressIndicator(strokeWidth: 2)))
            : IconButton(
                icon: const Icon(Icons.arrow_forward, color: Colors.blueAccent),
                onPressed: _handleSearch,
              ),
          border: InputBorder.none,
          contentPadding: const EdgeInsets.symmetric(vertical: 12),
        ),
        onSubmitted: (_) => _handleSearch(),
      ),
    );
  }

  Widget _buildPortfolioSummary() {
    double totalMarketValue = 0;
    double totalProfit = 0;
    
    if (_portfolio != null) {
      for (var asset in _portfolio!) {
        totalMarketValue += asset.quantity * asset.currentPrice;
        totalProfit += asset.profit;
      }
    }

    final profitColor = totalProfit >= 0 ? Colors.greenAccent : Colors.redAccent;

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [Colors.blue[700]!, Colors.blue[900]!],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.blue.withOpacity(0.2),
            blurRadius: 10,
            offset: const Offset(0, 4),
          )
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Total Portfolio Value',
            style: TextStyle(color: Colors.white70, fontSize: 14),
          ),
          const SizedBox(height: 4),
          Text(
            '\$${NumberFormat('#,##0.00').format(totalMarketValue)}',
            style: const TextStyle(
              color: Colors.white,
              fontSize: 32,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              const Text('Today Profit: ', style: TextStyle(color: Colors.white60, fontSize: 14)),
              Text(
                '${totalProfit >= 0 ? "+" : ""}\$${NumberFormat('#,##0.00').format(totalProfit)}',
                style: TextStyle(color: profitColor, fontSize: 16, fontWeight: FontWeight.bold),
              ),
            ],
          )
        ],
      ),
    );
  }

  Widget _buildAssetList() {
    if (_portfolio == null || _portfolio!.isEmpty) {
      return Container(
        width: double.infinity,
        padding: const EdgeInsets.symmetric(vertical: 40),
        decoration: BoxDecoration(
          color: Colors.white.withOpacity(0.02),
          borderRadius: BorderRadius.circular(12),
        ),
        child: const Column(
          children: [
            Icon(Icons.pie_chart_outline, size: 48, color: Colors.grey),
            SizedBox(height: 12),
            Text('No assets found. Search and buy stocks!', style: TextStyle(color: Colors.grey)),
          ],
        ),
      );
    }

    return ListView.separated(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      itemCount: _portfolio!.length,
      separatorBuilder: (context, index) => const Divider(color: Colors.white10, height: 1),
      itemBuilder: (context, index) {
        final asset = _portfolio![index];
        final assetProfitColor = asset.profit >= 0 ? Colors.greenAccent : Colors.redAccent;

        return ListTile(
          contentPadding: const EdgeInsets.symmetric(vertical: 8),
          title: Row(
            children: [
              Text(
                asset.symbol,
                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18, color: Colors.white),
              ),
              const SizedBox(width: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: assetProfitColor.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(
                  '${asset.profitRate >= 0 ? "+" : ""}${asset.profitRate.toStringAsFixed(2)}%',
                  style: TextStyle(color: assetProfitColor, fontSize: 12, fontWeight: FontWeight.bold),
                ),
              )
            ],
          ),
          subtitle: Text(
            '${asset.quantity} shares · Avg \$${asset.averagePrice.toStringAsFixed(2)}',
            style: const TextStyle(color: Colors.grey, fontSize: 13),
          ),
          trailing: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                '\$${NumberFormat('#,##0.00').format(asset.currentPrice * asset.quantity)}',
                style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.white, fontSize: 16),
              ),
              Text(
                '${asset.profit >= 0 ? "+" : ""}\$${asset.profit.toStringAsFixed(2)}',
                style: TextStyle(fontSize: 12, color: assetProfitColor),
              ),
            ],
          ),
          onTap: () {
            Navigator.of(context).push(
              MaterialPageRoute(
                builder: (context) => StockDetailScreen(symbol: asset.symbol),
              ),
            );
          },
        );
      },
    );
  }
}