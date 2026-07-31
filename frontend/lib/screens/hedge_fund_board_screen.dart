import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'dart:convert';
import '../services/api_service.dart';
import '../widgets/ai_header_banner.dart';

class HedgeFundBoardScreen extends StatefulWidget {
  const HedgeFundBoardScreen({super.key});

  @override
  State<HedgeFundBoardScreen> createState() => _HedgeFundBoardScreenState();
}

class _HedgeFundBoardScreenState extends State<HedgeFundBoardScreen> with SingleTickerProviderStateMixin {
  final ApiService _apiService = ApiService();
  final TextEditingController _symbolController = TextEditingController(text: 'NVDA');
  
  late TabController _tabController;
  bool _isLoading = false;
  Map<String, dynamic>? _currentEvaluation;
  List<dynamic>? _historyLogs;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _fetchHistory();
  }

  @override
  void dispose() {
    _tabController.dispose();
    _symbolController.dispose();
    super.dispose();
  }

  Future<void> _fetchHistory() async {
    final history = await _apiService.getHedgeFundBoardHistory(limit: 50);
    if (mounted) {
      setState(() {
        _historyLogs = history;
      });
    }
  }

  Future<void> _evaluateSymbol() async {
    final symbol = _symbolController.text.trim().toUpperCase();
    if (symbol.isEmpty) return;

    setState(() => _isLoading = true);
    final res = await _apiService.evaluateHedgeFundBoard(symbol);
    if (mounted) {
      setState(() {
        _currentEvaluation = res;
        _isLoading = false;
      });
      _fetchHistory();
    }
  }

  Future<void> _runBatchSimulation() async {
    setState(() => _isLoading = true);
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('🤖 관리자 일괄 AI 헤지펀드 시뮬레이션 구동 시작...')),
    );
    final res = await _apiService.simulateBatchHedgeFund();
    if (mounted) {
      setState(() => _isLoading = false);
      if (res != null && res['status'] == 'success') {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('✅ 시뮬레이션 완료! 총 ${res['count']}개 종목 진단 기록이 반영되었습니다.')),
        );
        _fetchHistory();
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0F172A),
      appBar: AppBar(
        title: const Text('🏛️ AI 헤지펀드 이사회 대시보드 (Admin)'),
        backgroundColor: const Color(0xFF1E293B),
        bottom: TabBar(
          controller: _tabController,
          indicatorColor: Colors.cyanAccent,
          labelColor: Colors.cyanAccent,
          unselectedLabelColor: Colors.grey,
          tabs: const [
            Tab(icon: Icon(Icons.psychology), text: '이사회 실시간 진단'),
            Tab(icon: Icon(Icons.history_edu), text: '이사회 시뮬레이션 거래 내역'),
          ],
        ),
      ),
      body: Column(
        children: [
          const AiHeaderBanner(),
          Expanded(
            child: TabBarView(
              controller: _tabController,
              children: [
                _buildLiveBoardTab(),
                _buildHistoryTab(),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildLiveBoardTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 1. 종목 입력 및 일괄 시뮬레이션 액션 바
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: const Color(0xFF1E293B),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: Colors.white12),
            ),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _symbolController,
                    style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                    decoration: InputDecoration(
                      labelText: '종목 코드 (예: NVDA, TSLA, AAPL)',
                      labelStyle: const TextStyle(color: Colors.grey),
                      filled: true,
                      fillColor: const Color(0xFF0F172A),
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                ElevatedButton.icon(
                  onPressed: _isLoading ? null : _evaluateSymbol,
                  icon: const Icon(Icons.gavel, color: Colors.black),
                  label: const Text('이사회 소환 진단', style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold)),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.cyanAccent,
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                ),
                const SizedBox(width: 12),
                OutlinedButton.icon(
                  onPressed: _isLoading ? null : _runBatchSimulation,
                  icon: const Icon(Icons.play_circle_fill, color: Colors.amberAccent),
                  label: const Text('일괄 시뮬레이션', style: TextStyle(color: Colors.amberAccent, fontWeight: FontWeight.bold)),
                  style: OutlinedButton.styleFrom(
                    side: const BorderSide(color: Colors.amberAccent),
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),

          if (_isLoading)
            const Center(child: Padding(padding: EdgeInsets.all(40), child: CircularProgressIndicator()))
          else if (_currentEvaluation != null)
            _buildEvaluationReport(_currentEvaluation!)
          else
            const Center(
              child: Padding(
                padding: EdgeInsets.all(40),
                child: Text('종목을 입력하고 [이사회 소환 진단] 버튼을 누르거나 [일괄 시뮬레이션]을 실행하세요.', style: TextStyle(color: Colors.grey)),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildEvaluationReport(Map<String, dynamic> data) {
    final symbol = data['symbol'] ?? '';
    final action = data['final_action'] ?? 'HOLD';
    final score = (data['confidence_score'] as num?)?.toDouble() ?? 50.0;
    final qty = data['target_quantity'] ?? 0;
    final rationale = data['decision_rationale'] ?? '';
    final signals = data['agent_signals'] as Map<String, dynamic>? ?? {};

    Color actionColor = Colors.grey;
    if (action == 'BUY') actionColor = Colors.greenAccent;
    if (action == 'SELL') actionColor = Colors.redAccent;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // PM 최종 결의안 카너
        Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            gradient: LinearGradient(
              colors: [actionColor.withOpacity(0.2), const Color(0xFF1E293B)],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: actionColor.withOpacity(0.5)),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text('👑 PORTFOLIO MANAGER 결의안: $symbol', style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                    decoration: BoxDecoration(color: actionColor, borderRadius: BorderRadius.circular(20)),
                    child: Text(action, style: const TextStyle(color: Colors.black, fontWeight: FontWeight.bold, fontSize: 16)),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Text('확신 점수: ${score.toStringAsFixed(1)}점', style: TextStyle(color: actionColor, fontSize: 16, fontWeight: FontWeight.bold)),
                  const SizedBox(width: 20),
                  Text('권장 주문 수량: $qty주', style: const TextStyle(color: Colors.white70, fontSize: 16)),
                ],
              ),
              const SizedBox(height: 12),
              Text(rationale, style: const TextStyle(color: Colors.white, fontSize: 13, height: 1.4)),
            ],
          ),
        ),
        const SizedBox(height: 20),
        const Text('👥 AI 이사회 멤버별 의과 리포트', style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold)),
        const SizedBox(height: 12),

        // 각 멤버별 카드 리스트
        ...signals.entries.map((entry) {
          final sig = entry.value as Map<String, dynamic>;
          final name = sig['agent_name'] ?? entry.key;
          final rec = sig['recommendation'] ?? 'HOLD';
          final sScore = (sig['score'] as num?)?.toDouble() ?? 50.0;
          final rationaleText = sig['rationale'] ?? '';
          final details = sig['details'] as Map<String, dynamic>? ?? {};

          Color sigColor = Colors.grey;
          if (rec == 'BUY') sigColor = Colors.greenAccent;
          if (rec == 'SELL') sigColor = Colors.redAccent;

          return Card(
            color: const Color(0xFF1E293B),
            margin: const EdgeInsets.only(bottom: 12),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16), side: BorderSide(color: sigColor.withOpacity(0.3))),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(name, style: const TextStyle(color: Colors.cyanAccent, fontWeight: FontWeight.bold, fontSize: 15)),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                        decoration: BoxDecoration(color: sigColor.withOpacity(0.2), borderRadius: BorderRadius.circular(12), border: Border.all(color: sigColor)),
                        child: Text('$rec (${sScore.toStringAsFixed(1)}점)', style: TextStyle(color: sigColor, fontWeight: FontWeight.bold, fontSize: 12)),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(rationaleText, style: const TextStyle(color: Colors.white70, fontSize: 13)),
                  if (details.isNotEmpty && entry.key == 'GURU') ...[
                    const Divider(color: Colors.white10, height: 16),
                    Text(
                      '버핏(${details['buffett_verdict']}:${details['buffett_score']}점) | 캐시우드(${details['wood_verdict']}:${details['wood_score']}점) | 마이클버리(${details['burry_verdict']}:${details['burry_score']}점)',
                      style: const TextStyle(color: Colors.amberAccent, fontSize: 12, fontWeight: FontWeight.bold),
                    ),
                  ],
                ],
              ),
            ),
          );
        }).toList(),
      ],
    );
  }

  Widget _buildHistoryTab() {
    if (_historyLogs == null || _historyLogs!.isEmpty) {
      return const Center(child: Text('기록된 이사회 시뮬레이션 내역이 없습니다.', style: TextStyle(color: Colors.grey)));
    }

    return ListView.separated(
      padding: const EdgeInsets.all(16),
      itemCount: _historyLogs!.length,
      separatorBuilder: (_, __) => const SizedBox(height: 12),
      itemBuilder: (context, index) {
        final log = _historyLogs![index] as Map<String, dynamic>;
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
                    Text('주문 수량: $qty주', style: const TextStyle(color: Colors.white70, fontSize: 13)),
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
