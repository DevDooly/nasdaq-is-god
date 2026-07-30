import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/strategy.dart';
import 'dart:convert';

class StrategyScreen extends StatefulWidget {
  const StrategyScreen({super.key});

  @override
  State<StrategyScreen> createState() => _StrategyScreenState();
}

class _StrategyScreenState extends State<StrategyScreen> with SingleTickerProviderStateMixin {
  final ApiService _apiService = ApiService();
  late TabController _tabController;
  List<TradingStrategy>? _strategies;
  bool _isLoading = true;

  // 백테스트 & 하이브리드 진단용 입력 폼 상태
  final _symbolController = TextEditingController(text: 'AAPL');
  final FocusNode _symbolFocusNode = FocusNode();

  String _selectedStrategyType = 'HYBRID_ALL';
  String _selectedPeriod = '1y';
  double _techWeight = 0.6;
  double _buyThreshold = 60.0;
  double _sellThreshold = 40.0;

  bool _isBacktesting = false;
  Map<String, dynamic>? _backtestResult;

  bool _isEvaluatingHybrid = false;
  Map<String, dynamic>? _hybridResult;

  final List<Map<String, String>> _strategyOptions = [
    {'value': 'HYBRID_ALL', 'label': '🔥 하이브리드 종합 (지표 + AI 뉴스/트윗)'},
    {'value': 'HYBRID_RSI', 'label': '⚡ 하이브리드 RSI + AI 센티먼트'},
    {'value': 'SMA_CROSSOVER', 'label': '📈 이동평균 골든/데드 크로스'},
    {'value': 'RSI_REVERSAL', 'label': '📉 RSI 과매도/과매수 반등'},
    {'value': 'MACD_CROSSOVER', 'label': '📊 MACD 오실레이터 크로스'},
    {'value': 'BOLLINGER_BANDS', 'label': '📏 볼린저 밴드 이탈 반등'},
    {'value': 'DUAL_MOMENTUM', 'label': '🚀 듀얼 모멘텀 추세 추종'},
  ];

  final List<Map<String, String>> _periodOptions = [
    {'value': '6mo', 'label': '6개월'},
    {'value': '1y', 'label': '1년'},
    {'value': '2y', 'label': '2년'},
    {'value': '5y', 'label': '5년'},
  ];

  final List<String> _popularTickers = [
    'AAPL', 'TSLA', 'NVDA', 'QQQ', 'MSFT', 'AMZN', 'GOOGL', 'META', 'SPY', 'AMD', 'NFLX', 'INTC'
  ];

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _fetchStrategies();
  }

  @override
  void dispose() {
    _tabController.dispose();
    _symbolController.dispose();
    _symbolFocusNode.dispose();
    super.dispose();
  }

  Future<void> _fetchStrategies() async {
    setState(() => _isLoading = true);
    final data = await _apiService.getStrategies();
    if (mounted) {
      setState(() {
        _strategies = data?.map((item) => TradingStrategy.fromJson(item)).toList();
        _isLoading = false;
      });
    }
  }

  Future<void> _runBacktest() async {
    setState(() {
      _isBacktesting = true;
      _backtestResult = null;
    });

    final symbol = _symbolController.text.trim().toUpperCase();
    final params = {
      'tech_weight': _techWeight,
      'buy_threshold': _buyThreshold,
      'sell_threshold': _sellThreshold,
    };

    final res = await _apiService.runBacktest(
      symbol,
      _selectedStrategyType,
      params,
      period: _selectedPeriod,
    );

    if (mounted) {
      setState(() {
        _backtestResult = res;
        _isBacktesting = false;
      });
    }
  }

  Future<void> _evaluateHybrid() async {
    setState(() {
      _isEvaluatingHybrid = true;
      _hybridResult = null;
    });

    final symbol = _symbolController.text.trim().toUpperCase();
    final res = await _apiService.evaluateHybrid(
      symbol,
      _selectedStrategyType,
      _techWeight,
      _buyThreshold,
      _sellThreshold,
    );

    if (mounted) {
      setState(() {
        _hybridResult = res;
        _isEvaluatingHybrid = false;
      });
    }
  }

  void _showAddStrategyDialog() {
    final nameController = TextEditingController(text: '${_symbolController.text.toUpperCase()} $_selectedStrategyType');

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: const Color(0xFF1E293B),
        title: const Text('신규 자동매매 전략 등록', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: nameController,
                style: const TextStyle(color: Colors.white),
                decoration: const InputDecoration(labelText: '전략 명칭', labelStyle: TextStyle(color: Colors.grey)),
              ),
              const SizedBox(height: 12),
              Text('대상 종목: ${_symbolController.text.toUpperCase()}', style: const TextStyle(color: Color(0xFF06B6D4), fontWeight: FontWeight.bold)),
              Text('전략 타입: $_selectedStrategyType', style: const TextStyle(color: Colors.white70)),
            ],
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('취소')),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF06B6D4)),
            onPressed: () async {
              final params = {
                "tech_weight": _techWeight,
                "buy_threshold": _buyThreshold,
                "sell_threshold": _sellThreshold,
              };
              await _apiService.createStrategy({
                "name": nameController.text,
                "symbol": _symbolController.text.toUpperCase(),
                "strategy_type": _selectedStrategyType,
                "parameters": jsonEncode(params),
                "is_active": true,
              });
              if (context.mounted) {
                Navigator.pop(context);
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('🚀 신규 자동매매 전략이 활성화되었습니다!')),
                );
              }
              _fetchStrategies();
            },
            child: const Text('등록 및 활성화'),
          ),
        ],
      ),
    );
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
        backgroundColor: const Color(0xFF020617), // Slate 950
        appBar: AppBar(
          title: const Text('자동 매매 & 백테스팅 엔진'),
          backgroundColor: const Color(0xFF0F172A),
          bottom: TabBar(
            controller: _tabController,
            indicatorColor: const Color(0xFF06B6D4),
            labelColor: const Color(0xFF06B6D4),
            unselectedLabelColor: Colors.grey,
            tabs: const [
              Tab(icon: Icon(Icons.show_chart), text: '전략 시뮬레이터 & AI 진단'),
              Tab(icon: Icon(Icons.playlist_add_check), text: '활성화된 자동매매 목록'),
            ],
          ),
        ),
        body: TabBarView(
          controller: _tabController,
          children: [
            _buildSimulatorTab(),
            _buildActiveStrategiesTab(),
          ],
        ),
      ),
    );
  }

  Widget _buildSimulatorTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 1. 전략 설정 카드
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: const Color(0xFF0F172A),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: Colors.white10),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('⚙️ 시뮬레이션 및 전략 설정', style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
                const SizedBox(height: 16),
                
                // 티커 자동완성 및 기간 선택
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // 티커 자동완성 검색창
                    Expanded(
                      flex: 3,
                      child: RawAutocomplete<String>(
                        textEditingController: _symbolController,
                        focusNode: _symbolFocusNode,
                        optionsBuilder: (TextEditingValue textEditingValue) async {
                          final query = textEditingValue.text.trim().toUpperCase();
                          if (query.isEmpty) return const Iterable<String>.empty();
                          
                          final matches = _popularTickers.where((t) => t.contains(query)).toList();
                          final searchRes = await _apiService.searchStock(query);
                          if (searchRes != null && searchRes['symbol'] != null) {
                            final sym = searchRes['symbol'] as String;
                            if (!matches.contains(sym)) matches.insert(0, sym);
                          }
                          return matches;
                        },
                        onSelected: (String selection) {
                          setState(() {
                            _symbolController.text = selection;
                          });
                        },
                        optionsViewBuilder: (context, onSelected, options) {
                          return Align(
                            alignment: Alignment.topLeft,
                            child: Material(
                              elevation: 8,
                              color: const Color(0xFF1E293B),
                              borderRadius: BorderRadius.circular(12),
                              child: SizedBox(
                                width: 220,
                                child: ListView.builder(
                                  padding: const EdgeInsets.symmetric(vertical: 4),
                                  shrinkWrap: true,
                                  itemCount: options.length,
                                  itemBuilder: (context, index) {
                                    final option = options.elementAt(index);
                                    return ListTile(
                                      dense: true,
                                      title: Text(option, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                                      leading: const Icon(Icons.show_chart, color: Color(0xFF06B6D4), size: 18),
                                      onTap: () => onSelected(option),
                                    );
                                  },
                                ),
                              ),
                            ),
                          );
                        },
                        fieldViewBuilder: (context, controller, focusNode, onEditingComplete) {
                          return TextField(
                            controller: controller,
                            focusNode: focusNode,
                            onEditingComplete: onEditingComplete,
                            style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                            decoration: InputDecoration(
                              labelText: '종목 티커 (자동완성)',
                              labelStyle: const TextStyle(color: Colors.grey),
                              prefixIcon: const Icon(Icons.search, color: Color(0xFF06B6D4)),
                              filled: true,
                              fillColor: const Color(0xFF1E293B),
                              border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
                            ),
                          );
                        },
                      ),
                    ),
                    const SizedBox(width: 12),
                    // 백테스트 기간 선택
                    Expanded(
                      flex: 2,
                      child: DropdownButtonFormField<String>(
                        value: _selectedPeriod,
                        dropdownColor: const Color(0xFF1E293B),
                        style: const TextStyle(color: Colors.white, fontSize: 13, fontWeight: FontWeight.bold),
                        decoration: InputDecoration(
                          labelText: '테스트 기간',
                          labelStyle: const TextStyle(color: Colors.grey),
                          filled: true,
                          fillColor: const Color(0xFF1E293B),
                          border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
                        ),
                        items: _periodOptions.map((opt) {
                          return DropdownMenuItem<String>(
                            value: opt['value'],
                            child: Text(opt['label']!),
                          );
                        }).toList(),
                        onChanged: (val) {
                          if (val != null) setState(() => _selectedPeriod = val);
                        },
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                
                // 매매 기법 선택
                DropdownButtonFormField<String>(
                  value: _selectedStrategyType,
                  dropdownColor: const Color(0xFF1E293B),
                  style: const TextStyle(color: Colors.white, fontSize: 13),
                  decoration: InputDecoration(
                    labelText: '매매 기법 선택',
                    labelStyle: const TextStyle(color: Colors.grey),
                    filled: true,
                    fillColor: const Color(0xFF1E293B),
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
                  ),
                  items: _strategyOptions.map((opt) {
                    return DropdownMenuItem<String>(
                      value: opt['value'],
                      child: Text(opt['label']!, overflow: TextOverflow.ellipsis),
                    );
                  }).toList(),
                  onChanged: (val) {
                    if (val != null) setState(() => _selectedStrategyType = val);
                  },
                ),
                
                if (_selectedStrategyType.startsWith('HYBRID')) ...[
                  const SizedBox(height: 16),
                  Text('기술적 지표 가중치: ${(_techWeight * 100).toInt()}% (AI 센티먼트: ${((1 - _techWeight) * 100).toInt()}%)', style: const TextStyle(color: Colors.white70)),
                  Slider(
                    value: _techWeight,
                    min: 0.1,
                    max: 0.9,
                    divisions: 8,
                    activeColor: const Color(0xFF06B6D4),
                    onChanged: (val) => setState(() => _techWeight = val),
                  ),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text('매수 임계점: ${_buyThreshold.toInt()}점 이상', style: const TextStyle(color: Colors.greenAccent, fontSize: 12)),
                            Slider(
                              value: _buyThreshold,
                              min: 50.0,
                              max: 85.0,
                              divisions: 7,
                              activeColor: Colors.greenAccent,
                              onChanged: (val) => setState(() => _buyThreshold = val),
                            ),
                          ],
                        ),
                      ),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text('매도 임계점: ${_sellThreshold.toInt()}점 이하', style: const TextStyle(color: Colors.redAccent, fontSize: 12)),
                            Slider(
                              value: _sellThreshold,
                              min: 20.0,
                              max: 50.0,
                              divisions: 6,
                              activeColor: Colors.redAccent,
                              onChanged: (val) => setState(() => _sellThreshold = val),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ],
                const SizedBox(height: 16),
                Row(
                  children: [
                    Expanded(
                      child: ElevatedButton.icon(
                        icon: _isBacktesting ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white)) : const Icon(Icons.history_toggle_off),
                        label: Text('과거 ${_periodOptions.firstWhere((p) => p['value'] == _selectedPeriod)['label']} 백테스트 실행'),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: const Color(0xFF3B82F6),
                          padding: const EdgeInsets.symmetric(vertical: 14),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                        ),
                        onPressed: _isBacktesting ? null : _runBacktest,
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: ElevatedButton.icon(
                        icon: _isEvaluatingHybrid ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white)) : const Icon(Icons.psychology),
                        label: const Text('실시간 하이브리드 AI 진단'),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: const Color(0xFF10B981),
                          padding: const EdgeInsets.symmetric(vertical: 14),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                        ),
                        onPressed: _isEvaluatingHybrid ? null : _evaluateHybrid,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),

          // 2. 백테스트 성과 리포트 카드
          if (_backtestResult != null) _buildBacktestReportCard(),

          // 3. 하이브리드 AI 진단 리포트 카드
          if (_hybridResult != null) _buildHybridReportCard(),
        ],
      ),
    );
  }

  Widget _buildBacktestReportCard() {
    final res = _backtestResult!;
    final totalReturn = (res['total_return'] ?? 0.0) as num;
    final isPositive = totalReturn >= 0;
    final trades = (res['trades'] as List<dynamic>?) ?? [];

    return Container(
      margin: const EdgeInsets.only(bottom: 20),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF0F172A),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: isPositive ? Colors.green.withValues(alpha: 0.5) : Colors.red.withValues(alpha: 0.5)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('📊 과거 ${_periodOptions.firstWhere((p) => p['value'] == _selectedPeriod)['label']} 백테스팅 성과 리포트 (${res['symbol']})', style: const TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold)),
              ElevatedButton.icon(
                icon: const Icon(Icons.add_task, size: 16),
                label: const Text('전략으로 등록'),
                style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF06B6D4)),
                onPressed: _showAddStrategyDialog,
              ),
            ],
          ),
          const Divider(color: Colors.white10, height: 24),
          Row(
            children: [
              _buildMetricItem('누적 수익률', '${totalReturn > 0 ? "+" : ""}${totalReturn.toStringAsFixed(2)}%', isPositive ? Colors.greenAccent : Colors.redAccent),
              _buildMetricItem('연평균 (CAGR)', '${(res['cagr'] ?? 0).toStringAsFixed(2)}%', Colors.white),
              _buildMetricItem('최대 낙폭 (MDD)', '${(res['max_drawdown'] ?? 0).toStringAsFixed(2)}%', Colors.orangeAccent),
              _buildMetricItem('Sharpe Ratio', '${(res['sharpe_ratio'] ?? 0).toStringAsFixed(2)}', Colors.cyanAccent),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              _buildMetricItem('Buy&Hold 수익률', '${(res['benchmark_return'] ?? 0).toStringAsFixed(2)}%', Colors.grey),
              _buildMetricItem('승률 (Win Rate)', '${(res['win_rate'] ?? 0).toStringAsFixed(1)}%', Colors.white),
              _buildMetricItem('Profit Factor', '${(res['profit_factor'] ?? 0).toStringAsFixed(2)}', Colors.white),
              _buildMetricItem('총 완료 거래 수', '${res['total_trades_count'] ?? 0} 회', Colors.white),
            ],
          ),
          if (trades.isNotEmpty) ...[
            const SizedBox(height: 16),
            const Text('📑 최근 시뮬레이션 매매 거래 기록', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 14)),
            const SizedBox(height: 8),
            Container(
              constraints: const BoxConstraints(maxHeight: 180),
              decoration: BoxDecoration(color: Colors.white.withValues(alpha: 0.03), borderRadius: BorderRadius.circular(12)),
              child: ListView.builder(
                shrinkWrap: true,
                itemCount: trades.length > 8 ? 8 : trades.length,
                itemBuilder: (context, index) {
                  final t = trades[index];
                  final isBuy = t['type'] == 'BUY';
                  final pnl = (t['pnl'] ?? 0.0) as num;
                  final pnlPct = (t['pnl_percent'] ?? 0.0) as num;
                  
                  return ListTile(
                    dense: true,
                    leading: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(color: isBuy ? Colors.green.withValues(alpha: 0.2) : Colors.red.withValues(alpha: 0.2), borderRadius: BorderRadius.circular(6)),
                      child: Text(t['type'], style: TextStyle(color: isBuy ? Colors.greenAccent : Colors.redAccent, fontWeight: FontWeight.bold, fontSize: 11)),
                    ),
                    title: Text('${t['date']} · \$${t['price']}', style: const TextStyle(color: Colors.white, fontSize: 13)),
                    trailing: isBuy
                        ? null
                        : Text(
                            '${pnl >= 0 ? "+" : ""}\$${pnl.toStringAsFixed(2)} (${pnlPct >= 0 ? "+" : ""}${pnlPct.toStringAsFixed(2)}%)',
                            style: TextStyle(color: pnl >= 0 ? Colors.greenAccent : Colors.redAccent, fontWeight: FontWeight.bold, fontSize: 13),
                          ),
                  );
                },
              ),
            )
          ]
        ],
      ),
    );
  }

  Widget _buildHybridReportCard() {
    final res = _hybridResult!;
    final action = res['action'] ?? 'HOLD';
    final hybridScore = (res['hybrid_score'] ?? 50.0) as num;
    final techScore = (res['technical_score'] ?? 50.0) as num;
    final sentScore = (res['sentiment_score'] ?? 50.0) as num;

    Color actionColor = Colors.grey;
    if (action == 'BUY') actionColor = Colors.greenAccent;
    if (action == 'SELL') actionColor = Colors.redAccent;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF0F172A),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: actionColor.withValues(alpha: 0.6)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('🤖 실시간 하이브리드 AI 진단 (${res['symbol']})', style: const TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold)),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
                decoration: BoxDecoration(color: actionColor.withValues(alpha: 0.2), borderRadius: BorderRadius.circular(20), border: Border.all(color: actionColor)),
                child: Text('최종 추천: $action', style: TextStyle(color: actionColor, fontWeight: FontWeight.bold, fontSize: 14)),
              )
            ],
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              _buildMetricItem('하이브리드 총점', '$hybridScore 점', actionColor),
              _buildMetricItem('기술적 지표 점수', '$techScore 점', Colors.cyanAccent),
              _buildMetricItem('AI 뉴스/소셜 점수', '$sentScore 점', Colors.purpleAccent),
            ],
          ),
          if (res['sentiment_summary'] != null && (res['sentiment_summary'] as String).isNotEmpty) ...[
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(color: Colors.white.withValues(alpha: 0.05), borderRadius: BorderRadius.circular(12)),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('💡 AI 분석 요약', style: TextStyle(color: Colors.cyanAccent, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 4),
                  Text(res['sentiment_summary'], style: const TextStyle(color: Colors.white70, fontSize: 13)),
                ],
              ),
            ),
          ]
        ],
      ),
    );
  }

  Widget _buildMetricItem(String label, String value, Color valueColor) {
    return Expanded(
      child: Container(
        margin: const EdgeInsets.symmetric(horizontal: 4),
        padding: const EdgeInsets.all(10),
        decoration: BoxDecoration(color: Colors.white.withValues(alpha: 0.03), borderRadius: BorderRadius.circular(10)),
        child: Column(
          children: [
            Text(label, style: const TextStyle(color: Colors.grey, fontSize: 11), textAlign: TextAlign.center),
            const SizedBox(height: 4),
            Text(value, style: TextStyle(color: valueColor, fontWeight: FontWeight.bold, fontSize: 15), textAlign: TextAlign.center),
          ],
        ),
      ),
    );
  }

  Widget _buildActiveStrategiesTab() {
    return _isLoading
        ? const Center(child: CircularProgressIndicator())
        : _strategies == null || _strategies!.isEmpty
            ? const Center(child: Text('등록된 자동매매 전략이 없습니다.', style: TextStyle(color: Colors.grey)))
            : ListView.builder(
                padding: const EdgeInsets.all(16),
                itemCount: _strategies!.length,
                itemBuilder: (context, index) {
                  final strategy = _strategies![index];
                  return Card(
                    color: Colors.white.withValues(alpha: 0.05),
                    margin: const EdgeInsets.only(bottom: 12),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                    child: ListTile(
                      contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
                      title: Text(strategy.name, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16)),
                      subtitle: Text('${strategy.symbol} · ${strategy.strategyType}', style: const TextStyle(color: Color(0xFF06B6D4))),
                      trailing: Switch(
                        value: strategy.isActive,
                        activeColor: const Color(0xFF06B6D4),
                        onChanged: (val) async {
                          await _apiService.toggleStrategy(strategy.id);
                          _fetchStrategies();
                        },
                      ),
                      onLongPress: () async {
                        final confirm = await showDialog<bool>(
                          context: context,
                          builder: (context) => AlertDialog(
                            backgroundColor: const Color(0xFF1E293B),
                            title: const Text('전략 삭제', style: TextStyle(color: Colors.white)),
                            content: Text("'${strategy.name}' 전략을 삭제하시겠습니까?", style: const TextStyle(color: Colors.white70)),
                            actions: [
                              TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('취소')),
                              ElevatedButton(
                                style: ElevatedButton.styleFrom(backgroundColor: Colors.redAccent),
                                onPressed: () => Navigator.pop(context, true),
                                child: const Text('삭제'),
                              ),
                            ],
                          ),
                        );
                        if (confirm == true) {
                          await _apiService.deleteStrategy(strategy.id);
                          _fetchStrategies();
                        }
                      },
                    ),
                  );
                },
              );
  }
}