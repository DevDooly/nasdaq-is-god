import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/indicator.dart';

class StockDetailScreen extends StatefulWidget {
  final String symbol;

  const StockDetailScreen({super.key, required this.symbol});

  @override
  State<StockDetailScreen> createState() => _StockDetailScreenState();
}

class _StockDetailScreenState extends State<StockDetailScreen> {
  final ApiService _apiService = ApiService();
  IndicatorData? _data;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _fetchIndicators();
  }

  Future<void> _fetchIndicators() async {
    setState(() => _isLoading = true);
    final json = await _apiService.getIndicators(widget.symbol);
    if (json != null && mounted) {
      setState(() {
        _data = IndicatorData.fromJson(json);
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('${widget.symbol} Analysis')),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _buildPriceSection(),
                  const SizedBox(height: 24),
                  _buildIndicatorCard('RSI (Relative Strength Index)', _buildRSIInfo()),
                  const SizedBox(height: 16),
                  _buildIndicatorCard('MACD', _buildMACDInfo()),
                  const SizedBox(height: 16),
                  _buildIndicatorCard('Bollinger Bands', _buildBollingerInfo()),
                ],
              ),
            ),
    );
  }

  Widget _buildPriceSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('Current Price', style: TextStyle(color: Colors.grey)),
        Text(
          '\$${_data?.price.toStringAsFixed(2)}',
          style: const TextStyle(fontSize: 32, fontWeight: FontWeight.bold),
        ),
        Text('Last updated: ${_data?.timestamp}', style: const TextStyle(fontSize: 12, color: Colors.grey)),
      ],
    );
  }

  Widget _buildIndicatorCard(String title, Widget content) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.05),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.white10),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.blueAccent)),
          const SizedBox(height: 12),
          content,
        ],
      ),
    );
  }

  Widget _buildRSIInfo() {
    final rsi = _data?.rsi;
    if (rsi == null) return const Text('No data');
    
    Color rsiColor = Colors.white;
    String status = 'Neutral';
    if (rsi >= 70) {
      rsiColor = Colors.redAccent;
      status = 'Overbought';
    } else if (rsi <= 30) {
      rsiColor = Colors.greenAccent;
      status = 'Oversold';
    }

    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(rsi.toStringAsFixed(2), style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: rsiColor)),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
          decoration: BoxDecoration(color: rsiColor.withOpacity(0.2), borderRadius: BorderRadius.circular(4)),
          child: Text(status, style: TextStyle(color: rsiColor, fontWeight: FontWeight.bold)),
        ),
      ],
    );
  }

  Widget _buildMACDInfo() {
    return Column(
      children: [
        _buildRow('MACD Line', _data?.macd.val),
        _buildRow('Signal Line', _data?.macd.signal),
        _buildRow('Histogram', _data?.macd.hist, isHighlight: true),
      ],
    );
  }

  Widget _buildBollingerInfo() {
    return Column(
      children: [
        _buildRow('Upper Band', _data?.bollinger.upper),
        _buildRow('Middle Band', _data?.bollinger.middle),
        _buildRow('Lower Band', _data?.bollinger.lower),
      ],
    );
  }

  Widget _buildRow(String label, double? value, {bool isHighlight = false}) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(color: Colors.white70)),
          Text(
            value?.toStringAsFixed(4) ?? '-',
            style: TextStyle(
              fontWeight: isHighlight ? FontWeight.bold : FontWeight.normal,
              color: isHighlight ? Colors.orangeAccent : Colors.white,
            ),
          ),
        ],
      ),
    );
  }
}
