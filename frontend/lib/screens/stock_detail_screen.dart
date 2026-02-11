import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import '../services/api_service.dart';
import '../models/indicator.dart';
import 'package:intl/intl.dart';

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
      backgroundColor: const Color(0xFF0F172A),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _buildPriceHeader(),
                  const SizedBox(height: 24),
                  _buildChartCard('Price History', _buildPriceChart()),
                  const SizedBox(height: 24),
                  _buildIndicatorCard('RSI (Relative Strength Index)', _buildRSISection()),
                  const SizedBox(height: 24),
                  _buildIndicatorCard('MACD & Bollinger', _buildTechnicalDetails()),
                  const SizedBox(height: 40),
                  _buildTradeButtons(),
                  const SizedBox(height: 40),
                ],
              ),
            ),
    );
  }

  Widget _buildTradeButtons() {
    return Row(
      children: [
        Expanded(
          child: ElevatedButton(
            onPressed: () => _showOrderDialog('BUY'),
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.greenAccent[700],
              padding: const EdgeInsets.symmetric(vertical: 16),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            ),
            child: const Text('BUY', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white)),
          ),
        ),
        const SizedBox(width: 16),
        Expanded(
          child: ElevatedButton(
            onPressed: () => _showOrderDialog('SELL'),
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.redAccent[700],
              padding: const EdgeInsets.symmetric(vertical: 16),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            ),
            child: const Text('SELL', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white)),
          ),
        ),
      ],
    );
  }

  void _showOrderDialog(String side) {
    final quantityController = TextEditingController(text: '1');
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: const Color(0xFF1E293B),
        title: Text('$side ${widget.symbol}', style: const TextStyle(color: Colors.white)),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: quantityController,
              keyboardType: TextInputType.number,
              style: const TextStyle(color: Colors.white),
              decoration: const InputDecoration(
                labelText: 'Quantity',
                labelStyle: TextStyle(color: Colors.grey),
                enabledBorder: UnderlineInputBorder(borderSide: BorderSide(color: Colors.white24)),
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel', style: TextStyle(color: Colors.grey)),
          ),
          ElevatedButton(
            onPressed: () async {
              final qty = double.tryParse(quantityController.text) ?? 0;
              if (qty <= 0) return;
              
              Navigator.pop(context);
              
              // 로딩 표시용 스낵바
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Processing order...'), duration: Duration(seconds: 1)),
              );

              final result = await _apiService.placeOrder(widget.symbol, qty, side);
              
              if (mounted) {
                if (result != null && result['status'] == 'success') {
                  // 성공 알림 (초록색)
                  ScaffoldMessenger.of(context).hideCurrentSnackBar();
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: Text('🎉 ${widget.symbol} $side Order Successful!'),
                      backgroundColor: Colors.green[600],
                      duration: const Duration(seconds: 3),
                    ),
                  );
                  // 성공 후 대시보드로 돌아가거나 화면 갱신 가능
                } else {
                  // 실패 알림 (빨간색)
                  ScaffoldMessenger.of(context).hideCurrentSnackBar();
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(
                      content: Text('❌ Order failed. Please check your balance or try again.'),
                      backgroundColor: Colors.redAccent,
                    ),
                  );
                }
              }
            },
            child: const Text('Confirm'),
          ),
        ],
      ),
    );
  }

  Widget _buildPriceHeader() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(widget.symbol, style: const TextStyle(fontSize: 14, color: Colors.blueAccent, fontWeight: FontWeight.bold)),
        Text(
          '\$${_data?.price.toStringAsFixed(2)}',
          style: const TextStyle(fontSize: 36, fontWeight: FontWeight.bold, color: Colors.white),
        ),
        Text('Last updated: ${DateFormat('MM/dd HH:mm').format(DateTime.parse(_data!.timestamp))}', 
             style: const TextStyle(fontSize: 12, color: Colors.grey)),
      ],
    );
  }

  Widget _buildChartCard(String title, Widget chart) {
    return Container(
      width: double.infinity,
      height: 300,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.03),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white10),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white70)),
          const SizedBox(height: 20),
          Expanded(child: chart),
        ],
      ),
    );
  }

  Widget _buildPriceChart() {
    if (_data == null || _data!.history.isEmpty) return const Center(child: Text('No history'));

    List<FlSpot> spots = [];
    for (int i = 0; i < _data!.history.length; i++) {
      spots.add(FlSpot(i.toDouble(), _data!.history[i].price));
    }

    return LineChart(
      LineChartData(
        gridData: const FlGridData(show: false),
        titlesData: const FlTitlesData(show: false),
        borderData: FlBorderData(show: false),
        lineBarsData: [
          LineChartBarData(
            spots: spots,
            isCurved: true,
            color: Colors.blueAccent,
            barWidth: 3,
            isStrokeCapRound: true,
            dotData: const FlDotData(show: false),
            belowBarData: BarAreaData(
              show: true,
              color: Colors.blueAccent.withOpacity(0.1),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildIndicatorCard(String title, Widget content) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.03),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white10),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.blueAccent)),
          const SizedBox(height: 16),
          content,
        ],
      ),
    );
  }

  Widget _buildRSISection() {
    final rsi = _data?.rsi;
    if (rsi == null) return const Text('N/A');

    Color color = Colors.white;
    String status = 'NEUTRAL';
    if (rsi >= 70) {
      color = Colors.redAccent;
      status = 'OVERBOUGHT';
    } else if (rsi <= 30) {
      color = Colors.greenAccent;
      status = 'OVERSOLD';
    }

    return Column(
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(rsi.toStringAsFixed(2), style: TextStyle(fontSize: 32, fontWeight: FontWeight.bold, color: color)),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              decoration: BoxDecoration(color: color.withOpacity(0.1), borderRadius: BorderRadius.circular(8)),
              child: Text(status, style: TextStyle(color: color, fontWeight: FontWeight.bold, fontSize: 12)),
            ),
          ],
        ),
        const SizedBox(height: 20),
        SizedBox(
          height: 60,
          child: _buildRSIChart(),
        )
      ],
    );
  }

  Widget _buildRSIChart() {
    List<FlSpot> spots = [];
    for (int i = 0; i < _data!.history.length; i++) {
      if (_data!.history[i].rsi != null) {
        spots.add(FlSpot(i.toDouble(), _data!.history[i].rsi!));
      }
    }

    return LineChart(
      LineChartData(
        gridData: const FlGridData(show: false),
        titlesData: const FlTitlesData(show: false),
        borderData: FlBorderData(show: false),
        minY: 0,
        maxY: 100,
        lineBarsData: [
          LineChartBarData(
            spots: spots,
            isCurved: true,
            color: Colors.orangeAccent,
            barWidth: 2,
            dotData: const FlDotData(show: false),
          ),
        ],
      ),
    );
  }

  Widget _buildTechnicalDetails() {
    return Column(
      children: [
        _buildRow('MACD Histogram', _data?.macd.hist),
        _buildRow('Bollinger Upper', _data?.bollinger.upper),
        _buildRow('Bollinger Lower', _data?.bollinger.lower),
      ],
    );
  }

  Widget _buildRow(String label, double? value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(color: Colors.white60)),
          Text(
            value?.toStringAsFixed(2) ?? '-',
            style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w500),
          ),
        ],
      ),
    );
  }
}
