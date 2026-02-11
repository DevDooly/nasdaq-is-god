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
  double _heldQuantity = 0;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _fetchInitialData();
  }

  Future<void> _fetchInitialData() async {
    setState(() => _isLoading = true);
    
    final results = await Future.wait([
      _apiService.getIndicators(widget.symbol),
      _apiService.getPortfolio(),
    ]);

    final indicatorJson = results[0] as Map<String, dynamic>?;
    final portfolioJson = results[1] as List<dynamic>?;

    if (mounted) {
      setState(() {
        if (indicatorJson != null) {
          _data = IndicatorData.fromJson(indicatorJson);
        }
        
        if (portfolioJson != null) {
          final assets = portfolioJson.map((item) => StockAsset.fromJson(item)).toList();
          final currentAsset = assets.cast<StockAsset?>().firstWhere(
            (a) => a?.symbol == widget.symbol, 
            orElse: () => null
          );
          _heldQuantity = currentAsset?.quantity ?? 0;
        }
        
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, result) {
        if (didPop) return;
        Navigator.of(context).pop();
      },
      child: Scaffold(
        appBar: AppBar(
          title: Text('${widget.symbol} Analysis'),
          leading: IconButton(
            icon: const Icon(Icons.arrow_back),
            onPressed: () => Navigator.of(context).pop(),
          ),
        ),
        backgroundColor: const Color(0xFF0F172A),
        body: _isLoading
            ? const Center(child: CircularProgressIndicator())
            : RefreshIndicator(
                onRefresh: _fetchInitialData,
                child: SingleChildScrollView(
                  physics: const AlwaysScrollableScrollPhysics(),
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
    final isSell = side.toUpperCase() == 'SELL';
    bool isButtonEnabled = true;

    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setDialogState) {
          // 💡 입력값 변경 감지 로직
          void validateInput() {
            final qty = double.tryParse(quantityController.text) ?? 0;
            final isValid = isSell ? (qty > 0 && qty <= _heldQuantity) : (qty > 0);
            if (isButtonEnabled != isValid) {
              setDialogState(() {
                isButtonEnabled = isValid;
              });
            }
          }

          return AlertDialog(
            backgroundColor: const Color(0xFF1E293B),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
            title: Text('$side ${widget.symbol}', style: const TextStyle(color: Colors.white)),
            content: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (isSell) ...[
                  Text(
                    'Available: $_heldQuantity shares',
                    style: const TextStyle(color: Colors.blueAccent, fontSize: 13, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 12),
                ],
                TextField(
                  controller: quantityController,
                  onChanged: (_) => validateInput(), // 💡 값이 바뀔 때마다 검증
                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                  style: const TextStyle(color: Colors.white, fontSize: 20),
                  decoration: InputDecoration(
                    labelText: 'Quantity',
                    labelStyle: const TextStyle(color: Colors.grey),
                    errorText: (isSell && (double.tryParse(quantityController.text) ?? 0) > _heldQuantity)
                        ? 'Insufficient quantity'
                        : null,
                    enabledBorder: const UnderlineInputBorder(borderSide: BorderSide(color: Colors.white24)),
                  ),
                ),
                if (isSell && _heldQuantity > 0) ...[
                  const SizedBox(height: 16),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [25, 50, 75, 100].map((pct) {
                      return InkWell(
                        onTap: () {
                          final calculated = (_heldQuantity * (pct / 100));
                          quantityController.text = calculated.toStringAsFixed(2);
                          validateInput(); // 💡 버튼 상태 업데이트
                        },
                        child: Container(
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                          decoration: BoxDecoration(
                            color: Colors.white.withOpacity(0.1),
                            borderRadius: BorderRadius.circular(6),
                          ),
                          child: Text('$pct%', style: const TextStyle(color: Colors.white70, fontSize: 12)),
                        ),
                      );
                    }).toList(),
                  ),
                ],
              ],
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(context),
                child: const Text('Cancel', style: TextStyle(color: Colors.grey)),
              ),
              ElevatedButton(
                onPressed: isButtonEnabled ? () async {
                  final qty = double.tryParse(quantityController.text) ?? 0;
                  Navigator.pop(context);
                  
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: Text('⏳ Processing $side order...'),
                      backgroundColor: Colors.blueGrey,
                      duration: const Duration(seconds: 1),
                    ),
                  );

                  final result = await _apiService.placeOrder(widget.symbol, qty, side);
                  
                  if (mounted) {
                    ScaffoldMessenger.of(context).clearSnackBars();
                    if (result != null && result['status'] == 'success') {
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(
                          content: Text('🎉 ${widget.symbol} $side order successful!'),
                          backgroundColor: Colors.green[700],
                          behavior: SnackBarBehavior.floating,
                        ),
                      );
                      await _fetchInitialData();
                    } else {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(
                          content: Text('❌ Order failed.'),
                          backgroundColor: Colors.redAccent,
                          behavior: SnackBarBehavior.floating,
                        ),
                      );
                    }
                  }
                } : null, // 💡 조건 미달 시 버튼 비활성화 (null)
                child: const Text('Confirm'),
              ),
            ],
          );
        },
      ),
    );
  }

  Widget _buildPriceHeader() {
    if (_data == null) return const SizedBox();
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
    if (_data == null) return const SizedBox();
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
