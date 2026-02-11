import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import '../services/api_service.dart';
import '../models/indicator.dart';
import '../models/asset.dart';
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
  Map<String, dynamic>? _sentiment;
  double _heldQuantity = 0;
  bool _isLoading = true;
  bool _isSentimentLoading = true;

  @override
  void initState() {
    super.initState();
    _fetchInitialData();
    _fetchSentiment();
  }

  Future<void> _fetchInitialData() async {
    setState(() => _isLoading = true);
    final results = await Future.wait([
      _apiService.getIndicators(widget.symbol),
      _apiService.getPortfolio(),
    ]);

    if (mounted) {
      setState(() {
        if (results[0] != null) _data = IndicatorData.fromJson(results[0] as Map<String, dynamic>);
        if (results[1] != null) {
          final assets = (results[1] as Map<String, dynamic>)['assets'] as List;
          final currentAsset = assets.map((i) => StockAsset.fromJson(i)).cast<StockAsset?>().firstWhere((a) => a?.symbol == widget.symbol, orElse: () => null);
          _heldQuantity = currentAsset?.quantity ?? 0;
        }
        _isLoading = false;
      });
    }
  }

  Future<void> _fetchSentiment() async {
    setState(() => _isSentimentLoading = true);
    final result = await _apiService.getStockSentiment(widget.symbol);
    if (mounted) {
      setState(() {
        _sentiment = result;
        _isSentimentLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, result) { if (!didPop) Navigator.of(context).pop(); },
      child: Scaffold(
        appBar: AppBar(title: Text('${widget.symbol} Analysis')),
        backgroundColor: const Color(0xFF0F172A),
        body: _isLoading
            ? const Center(child: CircularProgressIndicator())
            : RefreshIndicator(
                onRefresh: () => Future.wait([_fetchInitialData(), _fetchSentiment()]),
                child: SingleChildScrollView(
                  physics: const AlwaysScrollableScrollPhysics(),
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      _buildPriceHeader(),
                      const SizedBox(height: 24),
                      _buildAISentimentCard(),
                      const SizedBox(height: 24),
                      _buildChartCard('Price History', _buildPriceChart()),
                      const SizedBox(height: 24),
                      _buildIndicatorCard('RSI (Relative Strength Index)', _buildRSISection()),
                      const SizedBox(height: 24),
                      _buildIndicatorCard('Technical Summary', _buildTechnicalDetails()),
                      const SizedBox(height: 40),
                      _buildTradeButtons(),
                      const SizedBox(height: 40),
                    ],
                  ),
                ),
              ),
      ),
    );
  }

  Widget _buildAISentimentCard() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: LinearGradient(colors: [Colors.purple[900]!.withOpacity(0.5), Colors.blue[900]!.withOpacity(0.5)]),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.purpleAccent.withOpacity(0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Row(
            children: [
              Icon(Icons.auto_awesome, color: Colors.purpleAccent, size: 20),
              SizedBox(width: 8),
              Text('Gemini AI Market Sentiment', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
            ],
          ),
          const SizedBox(height: 16),
          if (_isSentimentLoading)
            const Center(child: LinearProgressIndicator())
          else if (_sentiment == null || _sentiment!['error'] != null)
            const Text('Sentiment analysis currently unavailable', style: TextStyle(color: Colors.grey))
          else ...[
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('${_sentiment!['score']}/100', style: const TextStyle(fontSize: 32, fontWeight: FontWeight.bold, color: Colors.white)),
                    Text(_sentiment!['sentiment'], style: TextStyle(color: _getSentimentColor(_sentiment!['sentiment']), fontWeight: FontWeight.bold)),
                  ],
                ),
                Expanded(
                  child: Padding(
                    padding: const EdgeInsets.only(left: 20),
                    child: Text(_sentiment!['summary'], style: const TextStyle(color: Colors.white70, fontSize: 13)),
                  ),
                ),
              ],
            ),
            const Divider(height: 24, color: Colors.white10),
            Text(_sentiment!['reason'] ?? '', style: const TextStyle(color: Colors.grey, fontSize: 12)),
          ]
        ],
      ),
    );
  }

  Color _getSentimentColor(String sentiment) {
    if (sentiment == 'Bullish') return Colors.greenAccent;
    if (sentiment == 'Bearish') return Colors.redAccent;
    return Colors.white70;
  }

  Widget _buildPriceHeader() {
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text(widget.symbol, style: const TextStyle(fontSize: 14, color: Colors.blueAccent, fontWeight: FontWeight.bold)),
      Text('\$${_data?.price.toStringAsFixed(2)}', style: const TextStyle(fontSize: 36, fontWeight: FontWeight.bold, color: Colors.white)),
      Text('Last updated: ${DateFormat('MM/dd HH:mm').format(DateTime.parse(_data!.timestamp))}', style: const TextStyle(fontSize: 12, color: Colors.grey)),
    ]);
  }

  Widget _buildChartCard(String title, Widget chart) {
    return Container(width: double.infinity, height: 250, padding: const EdgeInsets.all(16), decoration: BoxDecoration(color: Colors.white.withOpacity(0.03), borderRadius: BorderRadius.circular(16), border: Border.all(color: Colors.white10)), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text(title, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white70)), const SizedBox(height: 20), Expanded(child: chart)]));
  }

  Widget _buildPriceChart() {
    if (_data == null || _data!.history.isEmpty) return const Center(child: Text('No history'));
    List<FlSpot> spots = [];
    for (int i = 0; i < _data!.history.length; i++) { spots.add(FlSpot(i.toDouble(), _data!.history[i].price)); }
    return LineChart(LineChartData(gridData: const FlGridData(show: false), titlesData: const FlTitlesData(show: false), borderData: FlBorderData(show: false), lineBarsData: [LineChartBarData(spots: spots, isCurved: true, color: Colors.blueAccent, barWidth: 3, dotData: const FlDotData(show: false), belowBarData: BarAreaData(show: true, color: Colors.blueAccent.withOpacity(0.1)))]));
  }

  Widget _buildIndicatorCard(String title, Widget content) {
    return Container(width: double.infinity, padding: const EdgeInsets.all(16), decoration: BoxDecoration(color: Colors.white.withOpacity(0.03), borderRadius: BorderRadius.circular(16), border: Border.all(color: Colors.white10)), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text(title, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.blueAccent)), const SizedBox(height: 16), content]));
  }

  Widget _buildRSISection() {
    final rsi = _data?.rsi;
    if (rsi == null) return const Text('N/A');
    Color color = Colors.white; String status = 'NEUTRAL';
    if (rsi >= 70) { color = Colors.redAccent; status = 'OVERBOUGHT'; } else if (rsi <= 30) { color = Colors.greenAccent; status = 'OVERSOLD'; }
    return Column(children: [Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [Text(rsi.toStringAsFixed(2), style: TextStyle(fontSize: 32, fontWeight: FontWeight.bold, color: color)), Container(padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6), decoration: BoxDecoration(color: color.withOpacity(0.1), borderRadius: BorderRadius.circular(8)), child: Text(status, style: TextStyle(color: color, fontWeight: FontWeight.bold, fontSize: 12)))]), const SizedBox(height: 20), SizedBox(height: 60, child: _buildRSIChart())]);
  }

  Widget _buildRSIChart() {
    if (_data == null) return const SizedBox();
    List<FlSpot> spots = [];
    for (int i = 0; i < _data!.history.length; i++) { if (_data!.history[i].rsi != null) spots.add(FlSpot(i.toDouble(), _data!.history[i].rsi!)); }
    return LineChart(LineChartData(gridData: const FlGridData(show: false), titlesData: const FlTitlesData(show: false), borderData: FlBorderData(show: false), minY: 0, maxY: 100, lineBarsData: [LineChartBarData(spots: spots, isCurved: true, color: Colors.orangeAccent, barWidth: 2, dotData: const FlDotData(show: false))]));
  }

  Widget _buildTechnicalDetails() {
    return Column(children: [_buildRow('MACD Histogram', _data?.macd.hist), _buildRow('Bollinger Upper', _data?.bollinger.upper), _buildRow('Bollinger Lower', _data?.bollinger.lower)]);
  }

  Widget _buildRow(String label, double? value) {
    return Padding(padding: const EdgeInsets.symmetric(vertical: 6), child: Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [Text(label, style: const TextStyle(color: Colors.white60)), Text(value?.toStringAsFixed(2) ?? '-', style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w500))]));
  }

  Widget _buildTradeButtons() {
    return Row(children: [
      Expanded(child: ElevatedButton(onPressed: () => _showOrderDialog('BUY'), style: ElevatedButton.styleFrom(backgroundColor: Colors.greenAccent[700], padding: const EdgeInsets.symmetric(vertical: 16), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12))), child: const Text('BUY', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white)))),
      const SizedBox(width: 16),
      Expanded(child: ElevatedButton(onPressed: () => _showOrderDialog('SELL'), style: ElevatedButton.styleFrom(backgroundColor: Colors.redAccent[700], padding: const EdgeInsets.symmetric(vertical: 16), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12))), child: const Text('SELL', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white)))),
    ]);
  }

  void _showOrderDialog(String side) {
    final quantityController = TextEditingController(text: '1');
    final isSell = side.toUpperCase() == 'SELL';
    bool isButtonEnabled = true;
    showDialog(context: context, builder: (context) => StatefulBuilder(builder: (context, setDialogState) {
      void validateInput() {
        final qty = double.tryParse(quantityController.text) ?? 0;
        final isValid = isSell ? (qty > 0 && qty <= _heldQuantity) : (qty > 0);
        if (isButtonEnabled != isValid) setDialogState(() { isButtonEnabled = isValid; });
      }
      return AlertDialog(backgroundColor: const Color(0xFF1E293B), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)), title: Text('$side ${widget.symbol}', style: const TextStyle(color: Colors.white)), content: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
        if (isSell) ...[Text('Available: $_heldQuantity shares', style: const TextStyle(color: Colors.blueAccent, fontSize: 13, fontWeight: FontWeight.bold)), const SizedBox(height: 12)],
        TextField(controller: quantityController, onChanged: (_) => validateInput(), keyboardType: const TextInputType.numberWithOptions(decimal: true), style: const TextStyle(color: Colors.white, fontSize: 20), decoration: InputDecoration(labelText: 'Quantity', labelStyle: const TextStyle(color: Colors.grey), errorText: (isSell && (double.tryParse(quantityController.text) ?? 0) > _heldQuantity) ? 'Insufficient quantity' : null, enabledBorder: const UnderlineInputBorder(borderSide: BorderSide(color: Colors.white24)))),
        if (isSell && _heldQuantity > 0) ...[const SizedBox(height: 16), Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [25, 50, 75, 100].map((pct) => InkWell(onTap: () { quantityController.text = (_heldQuantity * (pct / 100)).toStringAsFixed(2); validateInput(); }, child: Container(padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6), decoration: BoxDecoration(color: Colors.white.withOpacity(0.1), borderRadius: BorderRadius.circular(6)), child: Text('$pct%', style: const TextStyle(color: Colors.white70, fontSize: 12))))).toList())]
      ]), actions: [
        TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel', style: TextStyle(color: Colors.grey))),
        ElevatedButton(onPressed: isButtonEnabled ? () async {
          final qty = double.tryParse(quantityController.text) ?? 0;
          Navigator.pop(context);
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('⏳ Processing $side order...'), backgroundColor: Colors.blueGrey, duration: const Duration(seconds: 1)));
          final result = await _apiService.placeOrder(widget.symbol, qty, side);
          if (mounted) {
            ScaffoldMessenger.of(context).clearSnackBars();
            if (result != null && result['status'] == 'success') {
              ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('🎉 ${widget.symbol} $side successful!'), backgroundColor: Colors.green[700], behavior: SnackBarBehavior.floating));
              await _fetchInitialData();
            } else { ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('❌ Order failed.'), backgroundColor: Colors.redAccent, behavior: SnackBarBehavior.floating)); }
          }
        } : null, child: const Text('Confirm'))
      ]);
    }));
  }
}