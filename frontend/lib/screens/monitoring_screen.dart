import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../widgets/ai_header_banner.dart';

class MonitoringScreen extends StatefulWidget {
  const MonitoringScreen({super.key});

  @override
  State<MonitoringScreen> createState() => _MonitoringScreenState();
}

class _MonitoringScreenState extends State<MonitoringScreen> {
  final ApiService _apiService = ApiService();
  final TextEditingController _symbolController = TextEditingController();
  final TextEditingController _guruNameController = TextEditingController();
  final TextEditingController _guruHandleController = TextEditingController();
  final TextEditingController _guruSymbolsController = TextEditingController(text: 'TSLA,NVDA');

  bool _isLoading = true;
  List<String> _symbols = [];
  List<dynamic> _gurus = [];
  bool _batchRunning = false;

  @override
  void initState() {
    super.initState();
    _fetchTargets();
  }

  @override
  void dispose() {
    _symbolController.dispose();
    _guruNameController.dispose();
    _guruHandleController.dispose();
    _guruSymbolsController.dispose();
    super.dispose();
  }

  Future<void> _fetchTargets() async {
    setState(() => _isLoading = true);
    final data = await _apiService.getMonitoringTargets();
    if (mounted) {
      setState(() {
        if (data != null) {
          _symbols = List<String>.from(data['symbols'] ?? []);
          _gurus = List<dynamic>.from(data['gurus'] ?? []);
          _batchRunning = data['batch_running'] ?? false;
        }
        _isLoading = false;
      });
    }
  }

  Future<void> _addSymbol() async {
    final sym = _symbolController.text.trim().toUpperCase();
    if (sym.isEmpty) return;

    final ok = await _apiService.manageSymbolTarget(sym, 'ADD');
    if (ok) {
      _symbolController.clear();
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('✅ 종목 [$sym] 모니터링 대상 추가 완료')));
      _fetchTargets();
    }
  }

  Future<void> _removeSymbol(String sym) async {
    final ok = await _apiService.manageSymbolTarget(sym, 'REMOVE');
    if (ok) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('🗑️ 종목 [$sym] 모니터링 해제 완료')));
      _fetchTargets();
    }
  }

  Future<void> _toggleGuru(String handle) async {
    final ok = await _apiService.manageGuruTarget(handle: handle, action: 'TOGGLE');
    if (ok) {
      _fetchTargets();
    }
  }

  Future<void> _addGuru() async {
    final name = _guruNameController.text.trim();
    final handle = _guruHandleController.text.trim();
    final targetSyms = _guruSymbolsController.text.trim();

    if (name.isEmpty || handle.isEmpty) return;

    final ok = await _apiService.manageGuruTarget(
      name: name,
      handle: handle,
      targetSymbols: targetSyms,
      action: 'ADD',
    );

    if (ok) {
      _guruNameController.clear();
      _guruHandleController.clear();
      Navigator.pop(context);
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('✅ 거장 [$name] 등록 완료')));
      _fetchTargets();
    }
  }

  Future<void> _removeGuru(String handle) async {
    final ok = await _apiService.manageGuruTarget(handle: handle, action: 'REMOVE');
    if (ok) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('🗑️ 거장 [$handle] 모니터링 해제')));
      _fetchTargets();
    }
  }

  void _showAddGuruDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: const Color(0xFF1E293B),
        title: const Text('🧙‍♂️ 신규 관제 대가(Guru) 추가', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: _guruNameController,
              style: const TextStyle(color: Colors.white),
              decoration: const InputDecoration(labelText: '대가/기관 이름 (예: Jensen Huang)', labelStyle: TextStyle(color: Colors.grey)),
            ),
            TextField(
              controller: _guruHandleController,
              style: const TextStyle(color: Colors.white),
              decoration: const InputDecoration(labelText: '소셜/트윗 핸들 (예: @jensenhuang)', labelStyle: TextStyle(color: Colors.grey)),
            ),
            TextField(
              controller: _guruSymbolsController,
              style: const TextStyle(color: Colors.white),
              decoration: const InputDecoration(labelText: '관련 종목 코드 (예: NVDA,MSFT)', labelStyle: TextStyle(color: Colors.grey)),
            ),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('취소', style: TextStyle(color: Colors.grey))),
          ElevatedButton(
            onPressed: _addGuru,
            style: ElevatedButton.styleFrom(backgroundColor: Colors.cyanAccent),
            child: const Text('등록', style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold)),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0F172A),
      appBar: AppBar(
        title: const Text('🎯 모니터링 대상 관제 대시보드'),
        backgroundColor: const Color(0xFF1E293B),
      ),
      body: Column(
        children: [
          const AiHeaderBanner(),
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : RefreshIndicator(
                    onRefresh: _fetchTargets,
                    child: ListView(
                      padding: const EdgeInsets.all(16),
                      children: [
                        _buildStatusHeaderCard(),
                        const SizedBox(height: 20),
                        _buildSymbolsSection(),
                        const SizedBox(height: 24),
                        _buildGurusSection(),
                      ],
                    ),
                  ),
          ),
        ],
      ),
    );
  }

  Widget _buildStatusHeaderCard() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            _batchRunning ? Colors.greenAccent.withOpacity(0.15) : Colors.amberAccent.withOpacity(0.15),
            const Color(0xFF1E293B),
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: _batchRunning ? Colors.greenAccent.withOpacity(0.4) : Colors.amberAccent.withOpacity(0.4)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Row(
                children: [
                  Icon(Icons.radar, color: Colors.cyanAccent, size: 28),
                  SizedBox(width: 10),
                  Text('자동 수집 & 모니터링 파이프라인', style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
                ],
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                decoration: BoxDecoration(
                  color: _batchRunning ? Colors.greenAccent : Colors.amberAccent,
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Text(
                  _batchRunning ? 'LIVE RUNNING' : 'STANDBY',
                  style: const TextStyle(color: Colors.black, fontWeight: FontWeight.bold, fontSize: 12),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          const Text(
            '• 뉴스 자동 수집 (10분 주기)  |  • 거장 발언 수집 (5분 주기)  |  • AI 감성 분석 (15분 주기)',
            style: TextStyle(color: Colors.white70, fontSize: 13),
          ),
        ],
      ),
    );
  }

  Widget _buildSymbolsSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const Text('📈 모니터링 주식 종목 (Watchlist)', style: TextStyle(color: Colors.white, fontSize: 17, fontWeight: FontWeight.bold)),
            Text('총 ${_symbols.length}개 종목 관제 중', style: const TextStyle(color: Colors.grey, fontSize: 13)),
          ],
        ),
        const SizedBox(height: 12),

        // 종목 추가 필드
        Row(
          children: [
            Expanded(
              child: TextField(
                controller: _symbolController,
                style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                decoration: InputDecoration(
                  labelText: '신규 종목 추가 (예: AMD, COIN, PLTR)',
                  labelStyle: const TextStyle(color: Colors.grey),
                  filled: true,
                  fillColor: const Color(0xFF1E293B),
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                ),
              ),
            ),
            const SizedBox(width: 10),
            ElevatedButton.icon(
              onPressed: _addSymbol,
              icon: const Icon(Icons.add, color: Colors.black),
              label: const Text('추가', style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold)),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.cyanAccent,
                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              ),
            ),
          ],
        ),
        const SizedBox(height: 16),

        // 종목 칩 리스트
        Wrap(
          spacing: 10,
          runSpacing: 10,
          children: _symbols.map((sym) {
            return Chip(
              backgroundColor: const Color(0xFF1E293B),
              side: const BorderSide(color: Colors.cyanAccent),
              avatar: const CircleAvatar(backgroundColor: Colors.cyanAccent, child: Icon(Icons.show_chart, size: 14, color: Colors.black)),
              label: Text(sym, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
              deleteIcon: const Icon(Icons.close, size: 18, color: Colors.redAccent),
              onDeleted: () => _removeSymbol(sym),
            );
          }).toList(),
        ),
      ],
    );
  }

  Widget _buildGurusSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const Text('🧙‍♂️ 월가 거장 및 기관 관제 (Gurus)', style: TextStyle(color: Colors.white, fontSize: 17, fontWeight: FontWeight.bold)),
            OutlinedButton.icon(
              onPressed: _showAddGuruDialog,
              icon: const Icon(Icons.person_add, color: Colors.amberAccent, size: 18),
              label: const Text('대가 추가', style: TextStyle(color: Colors.amberAccent)),
              style: OutlinedButton.styleFrom(side: const BorderSide(color: Colors.amberAccent)),
            ),
          ],
        ),
        const SizedBox(height: 12),

        ..._gurus.map((guru) {
          final name = guru['name'] ?? '';
          final handle = guru['handle'] ?? '';
          final desc = guru['description'] ?? '';
          final targetSymbols = guru['target_symbols'] ?? '';
          final isActive = guru['is_active'] ?? true;

          return Card(
            color: const Color(0xFF1E293B),
            margin: const EdgeInsets.only(bottom: 12),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(16),
              side: BorderSide(color: isActive ? Colors.amberAccent.withOpacity(0.3) : Colors.white10),
            ),
            child: ListTile(
              contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              leading: CircleAvatar(
                backgroundColor: isActive ? Colors.amberAccent.withOpacity(0.2) : Colors.grey.withOpacity(0.2),
                child: Icon(Icons.person, color: isActive ? Colors.amberAccent : Colors.grey),
              ),
              title: Row(
                children: [
                  Text(name, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16)),
                  const SizedBox(width: 8),
                  Text(handle, style: const TextStyle(color: Colors.grey, fontSize: 13)),
                ],
              ),
              subtitle: Padding(
                padding: const EdgeInsets.only(top: 4),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(desc, style: const TextStyle(color: Colors.white70, fontSize: 12)),
                    const SizedBox(height: 4),
                    Text('관련 종목: $targetSymbols', style: const TextStyle(color: Colors.cyanAccent, fontSize: 11, fontWeight: FontWeight.bold)),
                  ],
                ),
              ),
              trailing: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Switch(
                    value: isActive,
                    activeColor: Colors.amberAccent,
                    onChanged: (val) => _toggleGuru(handle),
                  ),
                  IconButton(
                    icon: const Icon(Icons.delete_outline, color: Colors.redAccent),
                    onPressed: () => _removeGuru(handle),
                  ),
                ],
              ),
            ),
          );
        }).toList(),
      ],
    );
  }
}
