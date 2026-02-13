import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/trade_log.dart';
import 'package:intl/intl.dart';

class TradeHistoryScreen extends StatefulWidget {
  const TradeHistoryScreen({super.key});

  @override
  State<TradeHistoryScreen> createState() => _TradeHistoryScreenState();
}

class _TradeHistoryScreenState extends State<TradeHistoryScreen> {
  final ApiService _apiService = ApiService();
  List<TradeLog>? _history;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _fetchHistory();
  }

  Future<void> _fetchHistory() async {
    setState(() => _isLoading = true);
    final data = await _apiService.getTradeHistory();
    if (mounted) {
      setState(() {
        _history = data?.map((item) => TradeLog.fromJson(item)).toList();
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('거래 내역')),
      backgroundColor: const Color(0xFF0F172A),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _history == null || _history!.isEmpty
              ? const Center(child: Text('거래 내역이 없습니다', style: TextStyle(color: Colors.grey)))
              : ListView.separated(
                  padding: const EdgeInsets.all(16),
                  itemCount: _history!.length,
                  separatorBuilder: (context, index) => const Divider(color: Colors.white10),
                  itemBuilder: (context, index) {
                    final log = _history![index];
                    final isBuy = log.side.toUpperCase() == 'BUY';
                    return ListTile(
                      contentPadding: EdgeInsets.zero,
                      leading: CircleAvatar(
                        backgroundColor: isBuy ? Colors.greenAccent.withOpacity(0.1) : Colors.redAccent.withOpacity(0.1),
                        child: Icon(
                          isBuy ? Icons.add : Icons.remove,
                          color: isBuy ? Colors.greenAccent : Colors.redAccent,
                        ),
                      ),
                      title: Text(
                        '${log.symbol} · ${isBuy ? '매수' : '매도'}',
                        style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.white),
                      ),
                      subtitle: Text(
                        DateFormat('yyyy-MM-dd HH:mm').format(log.executedAt),
                        style: const TextStyle(color: Colors.grey, fontSize: 12),
                      ),
                      trailing: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        crossAxisAlignment: CrossAxisAlignment.end,
                        children: [
                          Text(
                            '\$${NumberFormat('#,##0.00').format(log.totalAmount)}',
                            style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.white),
                          ),
                          Text(
                            '${log.quantity} 주 @ \$${log.price.toStringAsFixed(2)}',
                            style: const TextStyle(fontSize: 11, color: Colors.grey),
                          ),
                        ],
                      ),
                    );
                  },
                ),
    );
  }
}
