import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/trade_log.dart';
import '../widgets/ai_header_banner.dart';
import 'package:intl/intl.dart';

class TradeHistoryScreen extends StatefulWidget {
  const TradeHistoryScreen({super.key});

  @override
  State<TradeHistoryScreen> createState() => _TradeHistoryScreenState();
}

class _TradeHistoryScreenState extends State<TradeHistoryScreen> with SingleTickerProviderStateMixin {
  final ApiService _apiService = ApiService();
  late TabController _tabController;

  List<TradeLog>? _history;
  List<dynamic>? _boardLogs;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _fetchHistory();
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _fetchHistory() async {
    setState(() => _isLoading = true);
    final data = await _apiService.getTradeHistory();
    final bLogs = await _apiService.getHedgeFundBoardHistory(limit: 50);

    if (mounted) {
      setState(() {
        _history = data?.map((item) => TradeLog.fromJson(item)).toList();
        _boardLogs = bLogs;
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
        if (Navigator.canPop(context)) {
          Navigator.pop(context);
        }
      },
      child: Scaffold(
        appBar: AppBar(
          title: const Text('거래 내역 & AI 이사회 기밀로그'),
          backgroundColor: const Color(0xFF1E293B),
          bottom: TabBar(
            controller: _tabController,
            indicatorColor: Colors.cyanAccent,
            labelColor: Colors.cyanAccent,
            unselectedLabelColor: Colors.grey,
            tabs: const [
              Tab(icon: Icon(Icons.receipt_long), text: '실전/모의 체결 내역'),
              Tab(icon: Icon(Icons.psychology), text: 'AI 이사회 시뮬레이션 로그'),
            ],
          ),
        ),
        backgroundColor: const Color(0xFF0F172A),
        body: _isLoading
            ? const Center(child: CircularProgressIndicator())
            : Column(
                children: [
                  const AiHeaderBanner(),
                  Expanded(
                    child: TabBarView(
                      controller: _tabController,
                      children: [
                        _buildUserTradeList(),
                        _buildBoardLogList(),
                      ],
                    ),
                  ),
                ],
              ),
      ),
    );
  }

  Widget _buildUserTradeList() {
    if (_history == null || _history!.isEmpty) {
      return const Center(child: Text('체결된 거래 내역이 없습니다', style: TextStyle(color: Colors.grey)));
    }
    return ListView.separated(
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
    );
  }

  Widget _buildBoardLogList() {
    if (_boardLogs == null || _boardLogs!.isEmpty) {
      return const Center(child: Text('기록된 AI 이사회 시뮬레이션 내역이 없습니다.', style: TextStyle(color: Colors.grey)));
    }

    return ListView.separated(
      padding: const EdgeInsets.all(16),
      itemCount: _boardLogs!.length,
      separatorBuilder: (_, __) => const SizedBox(height: 12),
      itemBuilder: (context, index) {
        final log = _boardLogs![index] as Map<String, dynamic>;
        final symbol = log['symbol'] ?? '';
        final action = log['final_action'] ?? 'HOLD';
        final score = (log['confidence_score'] as num?)?.toDouble() ?? 50.0;
        final qty = log['target_quantity'] ?? 0;
        final rationale = log['decision_rationale'] ?? '';
        final createdAt = log['created_at'] != null ? DateTime.tryParse(log['created_at'].toString()) : null;

        Color actionColor = Colors.grey;
        if (action == 'BUY') actionColor = Colors.greenAccent;
        if (action == 'SELL') actionColor = Colors.redAccent;

        return Card(
          color: const Color(0xFF1E293B),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16), side: const BorderSide(color: Colors.white12)),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Row(
                      children: [
                        Text(symbol, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16)),
                        const SizedBox(width: 10),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                          decoration: BoxDecoration(color: actionColor.withOpacity(0.2), borderRadius: BorderRadius.circular(12), border: Border.all(color: actionColor)),
                          child: Text(action, style: TextStyle(color: actionColor, fontWeight: FontWeight.bold, fontSize: 12)),
                        ),
                      ],
                    ),
                    Text(
                      createdAt != null ? DateFormat('yyyy-MM-dd HH:mm').format(createdAt) : '',
                      style: const TextStyle(color: Colors.grey, fontSize: 12),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Row(
                  children: [
                    Text('이사회 확신 점수: ${score.toStringAsFixed(1)}점', style: TextStyle(color: actionColor, fontSize: 13, fontWeight: FontWeight.bold)),
                    const SizedBox(width: 16),
                    Text('권장 수량: $qty주', style: const TextStyle(color: Colors.white70, fontSize: 13)),
                  ],
                ),
                const SizedBox(height: 8),
                Text(rationale, style: const TextStyle(color: Colors.white60, fontSize: 12, height: 1.3)),
              ],
            ),
          ),
        );
      },
    );
  }
}
