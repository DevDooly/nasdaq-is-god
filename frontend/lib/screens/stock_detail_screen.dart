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
  List<dynamic>? _aiModels;
  String _selectedModel = 'models/gemini-2.0-flash';
  double _heldQuantity = 0;
  bool _isLoading = true;
  bool _isSentimentLoading = false;

  @override
  void initState() {
    super.initState();
    _fetchInitialData();
    _fetchModels();
  }

  Future<void> _fetchInitialData() async {
    setState(() => _isLoading = true);
    final results = await Future.wait([
      _apiService.getIndicators(widget.symbol),
      _apiService.getPortfolio(),
      _apiService.getStockSentiment(widget.symbol),
    ]);

    if (mounted) {
      setState(() {
        if (results[0] != null) _data = IndicatorData.fromJson(results[0] as Map<String, dynamic>);
        if (results[1] != null) {
          final assets = (results[1] as Map<String, dynamic>)['assets'] as List;
          final currentAsset = assets.map((i) => StockAsset.fromJson(i)).cast<StockAsset?>().firstWhere((a) => a?.symbol == widget.symbol, orElse: () => null);
          _heldQuantity = currentAsset?.quantity ?? 0;
        }
        _sentiment = results[2] as Map<String, dynamic>?;
        _isLoading = false;
      });
    }
  }

  Future<void> _fetchModels() async {
    final models = await _apiService.getAiModels();
    if (models != null && mounted) {
      setState(() {
        _aiModels = models;
        if (!models.any((m) => m['name'] == _selectedModel)) {
          _selectedModel = models.first['name'];
        }
      });
    }
  }

  Future<void> _runAnalysis({bool force = true}) async {
    setState(() => _isSentimentLoading = true);
    final result = await _apiService.getStockSentiment(
      widget.symbol, 
      model: _selectedModel,
      force: force
    );
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
        backgroundColor: const Color(0xFF020617),
        appBar: AppBar(
          title: Text('${widget.symbol} Terminal', style: const TextStyle(fontWeight: FontWeight.w900)),
          backgroundColor: Colors.transparent,
        ),
        body: _isLoading
            ? const Center(child: CircularProgressIndicator(color: Colors.cyanAccent))
            : RefreshIndicator(
                onRefresh: _fetchInitialData,
                child: SingleChildScrollView(
                  padding: const EdgeInsets.all(24),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      _buildPriceHeader(),
                      const SizedBox(height: 32),
                      _buildMainLayout(),
                      const SizedBox(height: 40),
                      _buildTradeActionRow(),
                      const SizedBox(height: 40),
                    ],
                  ),
                ),
              ),
      ),
    );
  }

  Widget _buildMainLayout() {
    return LayoutBuilder(builder: (context, constraints) {
      if (constraints.maxWidth > 900) {
        return Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Expanded(flex: 3, child: Column(children: [
            _buildChartCard('PRICE ACTION', _buildPriceChart()),
            const SizedBox(height: 24),
            _buildIndicatorGrid(),
          ])),
          const SizedBox(width: 24),
          Expanded(flex: 2, child: _buildAISentimentSection()),
        ]);
      } else {
        return Column(children: [
          _buildAISentimentSection(),
          const SizedBox(height: 24),
          _buildChartCard('PRICE ACTION', _buildPriceChart()),
          const SizedBox(height: 24),
          _buildIndicatorGrid(),
        ]);
      }
    });
  }

  Widget _buildPriceHeader() {
    if (_data == null) return const SizedBox();
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text('MARKET PRICE', style: TextStyle(color: Colors.cyanAccent.withOpacity(0.5), fontSize: 12, letterSpacing: 2)),
      Row(crossAxisAlignment: CrossAxisAlignment.end, children: [
        Text('\$${_data?.price.toStringAsFixed(2)}', style: const TextStyle(fontSize: 48, fontWeight: FontWeight.w900, color: Colors.white)),
        const SizedBox(width: 16),
        Padding(
          padding: const EdgeInsets.only(bottom: 8),
          child: _buildRSIBadge(),
        )
      ]),
      Text('TS: ${DateFormat('MM/dd HH:mm:ss').format(DateTime.parse(_data!.timestamp))}', style: const TextStyle(fontSize: 11, color: Colors.grey, fontFamily: 'monospace')),
    ]);
  }

  Widget _buildRSIBadge() {
    final rsi = _data?.rsi ?? 50;
    Color color = Colors.cyanAccent;
    String label = 'NEUTRAL';
    if (rsi >= 70) { color = Colors.redAccent; label = 'OVERBOUGHT'; }
    else if (rsi <= 30) { color = Colors.greenAccent; label = 'OVERSOLD'; }
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(color: color.withOpacity(0.1), borderRadius: BorderRadius.circular(8), border: Border.all(color: color.withOpacity(0.3))),
      child: Text(label, style: TextStyle(color: color, fontWeight: FontWeight.bold, fontSize: 12)),
    );
  }

  Widget _buildAISentimentSection() {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: _glassDecoration(color: Colors.purpleAccent.withOpacity(0.02)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
            const Text('AI QUANT ADVISOR', style: TextStyle(color: Colors.purpleAccent, fontSize: 12, fontWeight: FontWeight.bold, letterSpacing: 1)),
            if (_aiModels != null) _buildModelPicker(),
          ]),
          const SizedBox(height: 24),
          if (_isSentimentLoading)
            const Center(child: Padding(padding: EdgeInsets.all(40), child: CircularProgressIndicator(color: Colors.purpleAccent)))
          else if (_sentiment == null)
            _buildEmptyAIState()
          else if (_sentiment!['error'] != null)
            _buildAIErrorState()
          else
            _buildAIAnalysisResult(),
        ],
      ),
    );
  }

  Widget _buildModelPicker() {
    return DropdownButton<String>(
      value: _selectedModel,
      dropdownColor: const Color(0xFF0F172A),
      underline: const SizedBox(),
      icon: const Icon(Icons.bolt, color: Colors.purpleAccent, size: 16),
      style: const TextStyle(fontSize: 11, color: Colors.purpleAccent, fontWeight: FontWeight.bold),
      onChanged: (val) { if (val != null) setState(() => _selectedModel = val); },
      items: _aiModels!.map<DropdownMenuItem<String>>((dynamic m) => DropdownMenuItem(value: m['name'], child: Text(m['display_name'].toString().toUpperCase()))).toList(),
    );
  }

  Widget _buildEmptyAIState() {
    return Center(child: Column(children: [
      const Text('No recent analysis found', style: TextStyle(color: Colors.grey)),
      const SizedBox(height: 16),
      ElevatedButton.icon(onPressed: () => _runAnalysis(force: false), icon: const Icon(Icons.psychology), label: const Text('GENERATE INSIGHT'), style: ElevatedButton.styleFrom(backgroundColor: Colors.purpleAccent)),
    ]));
  }

  Widget _buildAIAnalysisResult() {
    final score = _sentiment!['score'] ?? 50;
    final sentiment = _sentiment!['sentiment'] ?? 'Neutral';
    final summary = _sentiment!['summary'] ?? '';
    final reason = _sentiment!['reason'] ?? '';
    final sources = _sentiment!['sources'] as List? ?? [];

    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Row(children: [
        Text('$score', style: const TextStyle(fontSize: 40, fontWeight: FontWeight.w900)),
        const Text('/100', style: TextStyle(color: Colors.grey, fontSize: 16)),
        const Spacer(),
        Text(sentiment.toUpperCase(), style: TextStyle(color: _getSentimentColor(sentiment), fontSize: 20, fontWeight: FontWeight.bold)),
      ]),
      const Divider(height: 32, color: Colors.white10),
      Text(summary, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold, height: 1.5)),
      const SizedBox(height: 12),
      Text(reason, style: const TextStyle(color: Colors.white70, fontSize: 13, height: 1.4)),
      const SizedBox(height: 24),
      if (sources.isNotEmpty) InkWell(onTap: () => _showSourcesDialog(sources), child: Text('VIEW ${sources.length} RAW SOURCES >', style: const TextStyle(color: Colors.blueAccent, fontSize: 11, fontWeight: FontWeight.bold, letterSpacing: 1))),
      const SizedBox(height: 24),
      Align(alignment: Alignment.centerRight, child: TextButton(onPressed: () => _runAnalysis(force: true), child: const Text('REFRESH ANALYTICS', style: TextStyle(fontSize: 11, color: Colors.purpleAccent)))),
    ]);
  }

  Widget _buildIndicatorGrid() {
    return GridView.count(
      crossAxisCount: MediaQuery.of(context).size.width > 600 ? 3 : 1,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      mainAxisSpacing: 16,
      crossAxisSpacing: 16,
      childAspectRatio: 2.5,
      children: [
        _buildSmallIndicatorCard('RSI (14)', _data?.rsi?.toStringAsFixed(2) ?? '-'),
        _buildSmallIndicatorCard('MACD HIST', _data?.macd.hist?.toStringAsFixed(2) ?? '-'),
        _buildSmallIndicatorCard('BB UPPER', _data?.bollinger.upper?.toStringAsFixed(2) ?? '-'),
      ],
    );
  }

  Widget _buildSmallIndicatorCard(String title, String value) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: _glassDecoration(),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, mainAxisAlignment: MainAxisAlignment.center, children: [
        Text(title, style: const TextStyle(color: Colors.grey, fontSize: 10, letterSpacing: 1)),
        const SizedBox(height: 4),
        Text(value, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold, fontFamily: 'monospace')),
      ]),
    );
  }

  Widget _buildChartCard(String title, Widget chart) {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: _glassDecoration(),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(title, style: const TextStyle(color: Colors.grey, fontSize: 12, fontWeight: FontWeight.bold, letterSpacing: 2)),
        const SizedBox(height: 32),
        SizedBox(height: 300, child: chart),
      ]),
    );
  }

  Widget _buildPriceChart() {
    if (_data == null || _data!.history.isEmpty) return const Center(child: Text('No data'));
    List<FlSpot> spots = _data!.history.asMap().entries.map((e) => FlSpot(e.key.toDouble(), e.value.price)).toList();
    return LineChart(LineChartData(
      gridData: const FlGridData(show: false),
      titlesData: const FlTitlesData(show: false),
      borderData: FlBorderData(show: false),
      lineBarsData: [
        LineChartBarData(
          spots: spots,
          isCurved: true,
          color: Colors.cyanAccent,
          barWidth: 4,
          dotData: const FlDotData(show: false),
          belowBarData: BarAreaData(show: true, gradient: LinearGradient(colors: [Colors.cyanAccent.withOpacity(0.2), Colors.transparent], begin: Alignment.topCenter, end: Alignment.bottomCenter)),
        ),
      ],
    ));
  }

  Widget _buildTradeActionRow() {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: _glassDecoration(color: Colors.blueAccent.withOpacity(0.05)),
      child: Row(children: [
        Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          const Text('CURRENT HOLDINGS', style: TextStyle(color: Colors.grey, fontSize: 11)),
          Text('${_heldQuantity.toStringAsFixed(2)} SHARES', style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w900)),
        ]),
        const Spacer(),
        ElevatedButton(onPressed: () => _showOrderDialog('BUY'), style: ElevatedButton.styleFrom(backgroundColor: Colors.greenAccent[700]), child: const Text('EXECUTE BUY')),
        const SizedBox(width: 12),
        ElevatedButton(onPressed: () => _showOrderDialog('SELL'), style: ElevatedButton.styleFrom(backgroundColor: Colors.redAccent[700]), child: const Text('EXECUTE SELL')),
      ]),
    );
  }

  void _showOrderDialog(String side) {
    final qtyController = TextEditingController(text: '1');
    showDialog(context: context, builder: (context) => AlertDialog(
      backgroundColor: const Color(0xFF0F172A),
      title: Text('$side ${widget.symbol}', style: const TextStyle(fontWeight: FontWeight.bold)),
      content: TextField(controller: qtyController, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: 'Quantity')),
      actions: [
        TextButton(onPressed: () => Navigator.pop(context), child: const Text('CANCEL')),
        ElevatedButton(onPressed: () async {
          final qty = double.tryParse(qtyController.text) ?? 0;
          Navigator.pop(context);
          final res = await _apiService.placeOrder(widget.symbol, qty, side);
          if (res != null) _fetchInitialData();
        }, child: const Text('CONFIRM')),
      ],
    ));
  }

  void _showSourcesDialog(List sources) {
    showDialog(context: context, builder: (context) => AlertDialog(
      backgroundColor: const Color(0xFF0F172A),
      title: const Text('RAW DATA SOURCES'),
      content: SizedBox(width: 500, child: ListView.separated(shrinkWrap: true, itemCount: sources.length, separatorBuilder: (_, __) => const Divider(color: Colors.white10), itemBuilder: (ctx, i) => Text('- ${sources[i]}', style: const TextStyle(fontSize: 12)))),
      actions: [TextButton(onPressed: () => Navigator.pop(context), child: const Text('CLOSE'))],
    ));
  }

  Color _getSentimentColor(String s) {
    if (s == 'Bullish') return Colors.greenAccent;
    if (s == 'Bearish') return Colors.redAccent;
    return Colors.white70;
  }

  BoxDecoration _glassDecoration({Color? color}) {
    return BoxDecoration(
      color: color ?? Colors.white.withOpacity(0.03),
      borderRadius: BorderRadius.circular(16),
      border: Border.all(color: Colors.white.withOpacity(0.08)),
    );
  }

  Widget _buildAIErrorState() {
    return Column(children: [
      const Icon(Icons.warning, color: Colors.orangeAccent),
      const SizedBox(height: 8),
      Text(_sentiment!['error'].toString(), style: const TextStyle(color: Colors.grey, fontSize: 12), textAlign: TextAlign.center),
      const SizedBox(height: 16),
      TextButton(onPressed: () => _runAnalysis(force: true), child: const Text('RETRY ANALYTICS')),
    ]);
  }
}