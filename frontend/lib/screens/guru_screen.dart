import 'package:flutter/material.dart';
import '../services/api_service.dart';
import 'package:intl/intl.dart';

class GuruScreen extends StatefulWidget {
  const GuruScreen({super.key});

  @override
  State<GuruScreen> createState() => _GuruScreenState();
}

class _GuruScreenState extends State<GuruScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  final ApiService _apiService = ApiService();
  
  List<dynamic> _gurus = [];
  List<dynamic> _insights = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
    _fetchData();
    _tabController.addListener(() {
      if (mounted) setState(() {});
    });
  }

  Future<void> _fetchData() async {
    setState(() => _isLoading = true);
    final results = await Future.wait([
      _apiService.getGurus(),
      _apiService.getGuruInsights(),
    ]);
    if (mounted) {
      setState(() {
        _gurus = results[0] ?? [];
        _insights = results[1] ?? [];
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF020617),
      appBar: AppBar(
        title: const Text('GURU ALPHA', style: TextStyle(fontWeight: FontWeight.w900, letterSpacing: 2)),
        backgroundColor: Colors.transparent,
        bottom: TabBar(
          controller: _tabController,
          indicatorColor: Colors.purpleAccent,
          labelColor: Colors.purpleAccent,
          unselectedLabelColor: Colors.grey,
          tabs: const [
            Tab(text: 'WATCH TIMELINE'),
            Tab(text: 'HISTORICAL ARCHIVE'),
            Tab(text: 'DIRECTORY & IMPACT'),
          ],
        ),
      ),
      body: _isLoading 
        ? const Center(child: CircularProgressIndicator(color: Colors.purpleAccent))
        : TabBarView(
            controller: _tabController,
            children: [
              _buildTimelineTab(),
              _buildArchiveTab(),
              _buildDirectoryTab(),
            ],
          ),
      floatingActionButton: (_tabController.index == 0 && _gurus.isNotEmpty) ? FloatingActionButton(
        onPressed: _showSimulateDialog,
        backgroundColor: Colors.purpleAccent,
        child: const Icon(Icons.psychology, color: Colors.white),
      ) : null,
    );
  }

  Widget _buildTimelineTab() {
    if (_insights.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.auto_awesome, size: 64, color: Colors.white10),
            const SizedBox(height: 16),
            const Text('No insights yet', style: TextStyle(color: Colors.grey)),
            const SizedBox(height: 24),
            ElevatedButton(onPressed: _showSimulateDialog, child: const Text('Simulate First Statement')),
          ],
        ),
      );
    }
    return RefreshIndicator(
      onRefresh: _fetchData,
      child: ListView.builder(
        padding: const EdgeInsets.all(24),
        itemCount: _insights.length,
        itemBuilder: (context, index) {
          final item = _insights[index];
          final insight = item['insight'];
          final score = insight['score'] ?? 50;
          return Container(
            margin: const EdgeInsets.only(bottom: 24),
            padding: const EdgeInsets.all(20),
            decoration: _glassDecoration(color: _getScoreColor(score).withOpacity(0.05)),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    CircleAvatar(
                      backgroundColor: Colors.purpleAccent.withOpacity(0.2), 
                      child: Text(item['guru_name'][0], style: const TextStyle(color: Colors.purpleAccent))
                    ),
                    const SizedBox(width: 12),
                    Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      Text(item['guru_name'], style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                      Text(item['guru_handle'], style: const TextStyle(color: Colors.grey, fontSize: 12)),
                    ]),
                    const Spacer(),
                    _buildImpactBadge(score),
                  ],
                ),
                const SizedBox(height: 16),
                if (insight['price_at_timestamp'] != null)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 12),
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                      decoration: BoxDecoration(color: Colors.cyanAccent.withOpacity(0.1), borderRadius: BorderRadius.circular(8)),
                      child: Text('PRICE AT STATEMENT: \$${insight['price_at_timestamp']}', style: const TextStyle(color: Colors.cyanAccent, fontWeight: FontWeight.bold, fontSize: 12, fontFamily: 'monospace')),
                    ),
                  ),
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(color: Colors.black26, borderRadius: BorderRadius.circular(8)),
                  child: Text(insight['content'], style: const TextStyle(fontSize: 14, height: 1.4, fontStyle: FontStyle.italic)),
                ),
                const SizedBox(height: 20),
                Row(children: [
                  const Icon(Icons.auto_awesome, size: 16, color: Colors.purpleAccent),
                  const SizedBox(width: 8),
                  Expanded(child: Text(insight['summary'], style: const TextStyle(color: Colors.purpleAccent, fontWeight: FontWeight.bold, fontSize: 15))),
                ]),
                const SizedBox(height: 8),
                Text(insight['reason'], style: const TextStyle(color: Colors.white70, fontSize: 13, height: 1.4)),
                if (insight['symbol'] != null) ...[
                  const SizedBox(height: 12),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(color: Colors.blueAccent.withOpacity(0.1), borderRadius: BorderRadius.circular(4)),
                    child: Text('RELATED: ${insight['symbol']}', style: const TextStyle(color: Colors.blueAccent, fontSize: 10, fontWeight: FontWeight.bold)),
                  ),
                ],
                const SizedBox(height: 16),
                Text(DateFormat('yyyy/MM/dd HH:mm').format(DateTime.parse(insight['timestamp'])), style: const TextStyle(color: Colors.grey, fontSize: 11)),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildArchiveTab() {
    // 날짜별로 그룹화
    Map<String, List<dynamic>> grouped = {};
    for (var item in _insights) {
      String date = DateFormat('yyyy-MM-dd').format(DateTime.parse(item['insight']['timestamp']));
      grouped.putIfAbsent(date, () => []).add(item);
    }
    var sortedDates = grouped.keys.toList()..sort((a, b) => b.compareTo(a));

    if (grouped.isEmpty) return const Center(child: Text('No historical data', style: TextStyle(color: Colors.grey)));

    return ListView.builder(
      padding: const EdgeInsets.all(24),
      itemCount: sortedDates.length,
      itemBuilder: (context, index) {
        String date = sortedDates[index];
        List<dynamic> dayInsights = grouped[date]!;
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 16),
              child: Text(date, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.purpleAccent)),
            ),
            ...dayInsights.map((item) {
              final insight = item['insight'];
              return Card(
                color: Colors.white.withOpacity(0.03),
                margin: const EdgeInsets.only(bottom: 8),
                child: ListTile(
                  leading: _buildSentimentIcon(insight['sentiment']),
                  title: Text(insight['content'], maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(fontSize: 13)),
                  subtitle: Text('${item['guru_name']} · \$${insight['price_at_timestamp'] ?? 'N/A'}', style: const TextStyle(fontSize: 11, color: Colors.grey)),
                  trailing: Text('${insight['score']}', style: TextStyle(color: _getScoreColor(insight['score']), fontWeight: FontWeight.bold)),
                  onTap: () => _showInsightDetail(item),
                ),
              );
            }).toList(),
          ],
        );
      },
    );
  }

  Widget _buildSentimentIcon(String sentiment) {
    if (sentiment == 'Bullish') return const Icon(Icons.trending_up, color: Colors.greenAccent, size: 20);
    if (sentiment == 'Bearish') return const Icon(Icons.trending_down, color: Colors.redAccent, size: 20);
    return const Icon(Icons.trending_flat, color: Colors.grey, size: 20);
  }

  void _showInsightDetail(dynamic item) {
    final insight = item['insight'];
    showDialog(context: context, builder: (context) => AlertDialog(
      backgroundColor: const Color(0xFF0F172A),
      title: Text(item['guru_name']),
      content: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(insight['content'], style: const TextStyle(fontStyle: FontStyle.italic)),
            const Divider(height: 32, color: Colors.white10),
            Text('SUMMARY: ${insight['summary']}', style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.purpleAccent)),
            const SizedBox(height: 8),
            Text('REASON: ${insight['reason']}', style: const TextStyle(fontSize: 13, color: Colors.white70)),
            const SizedBox(height: 20),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(color: Colors.cyanAccent.withOpacity(0.05), borderRadius: BorderRadius.circular(8), border: Border.all(color: Colors.cyanAccent.withOpacity(0.2))),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text('PRICE AT TIME', style: TextStyle(color: Colors.grey, fontSize: 11)),
                  Text('\$${insight['price_at_timestamp'] ?? 'N/A'}', style: const TextStyle(color: Colors.cyanAccent, fontWeight: FontWeight.bold, fontFamily: 'monospace')),
                ],
              ),
            ),
          ],
        ),
      ),
      actions: [TextButton(onPressed: () => Navigator.pop(context), child: const Text('CLOSE'))],
    ));
  }

  Widget _buildDirectoryTab() {
    return ListView.builder(
      padding: const EdgeInsets.all(24),
      itemCount: _gurus.length,
      itemBuilder: (context, index) {
        final guru = _gurus[index];
        return Container(
          margin: const EdgeInsets.only(bottom: 16),
          padding: const EdgeInsets.all(20),
          decoration: _glassDecoration(),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Expanded(
                    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      Text(guru['name'], style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                      Text(guru['handle'], style: const TextStyle(color: Colors.grey, fontSize: 13)),
                    ]),
                  ),
                  Column(crossAxisAlignment: CrossAxisAlignment.end, children: [
                    const Text('INFLUENCE', style: TextStyle(color: Colors.grey, fontSize: 10)),
                    Text('${guru['influence_score']}', style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w900, color: Colors.cyanAccent)),
                  ]),
                ],
              ),
              const SizedBox(height: 12),
              Text(guru['description'] ?? '', style: const TextStyle(color: Colors.white70, fontSize: 13)),
              const SizedBox(height: 20),
              Row(children: [
                const Icon(Icons.priority_high, size: 14, color: Colors.grey),
                const SizedBox(width: 8),
                const Text('Weight Adjustment', style: TextStyle(color: Colors.grey, fontSize: 12)),
              ]),
              Slider(
                value: (guru['influence_score'] as int).toDouble(),
                min: 0, max: 100,
                activeColor: Colors.cyanAccent,
                inactiveColor: Colors.white10,
                onChanged: (val) {
                  setState(() => guru['influence_score'] = val.toInt());
                },
                onChangeEnd: (val) async {
                  await _apiService.updateGuru(guru['id'], {'influence_score': val.toInt()});
                },
              ),
              Row(children: [
                const Icon(Icons.track_changes, size: 14, color: Colors.grey),
                const SizedBox(width: 8),
                Text('Target Symbols: ${guru['target_symbols']}', style: const TextStyle(color: Colors.grey, fontSize: 12, fontWeight: FontWeight.bold)),
              ]),
            ],
          ),
        );
      },
    );
  }

  void _showSimulateDialog() {
    if (_gurus.isEmpty) return;
    int selectedGuruId = _gurus.first['id'];
    final contentController = TextEditingController();

    showDialog(context: context, builder: (context) => StatefulBuilder(builder: (context, setDState) => AlertDialog(
      backgroundColor: const Color(0xFF0F172A),
      title: const Text('Simulate Alpha Statement'),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text('Select a Guru and enter their statement to analyze market impact.', style: TextStyle(color: Colors.grey, fontSize: 12)),
            const SizedBox(height: 16),
            DropdownButtonFormField<int>(
              value: selectedGuruId,
              isExpanded: true,
              dropdownColor: const Color(0xFF1E293B),
              decoration: const InputDecoration(labelText: 'Guru'),
              items: _gurus.map<DropdownMenuItem<int>>((g) => DropdownMenuItem(value: g['id'], child: Text(g['name']))).toList(),
              onChanged: (val) => setDState(() => selectedGuruId = val!),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: contentController,
              maxLines: 4,
              style: const TextStyle(fontSize: 14),
              decoration: const InputDecoration(
                hintText: 'e.g. Interest rates will remain high for a while.', 
                border: OutlineInputBorder(),
                alignLabelWithHint: true,
              ),
            ),
          ],
        ),
      ),
      actions: [
        TextButton(onPressed: () => Navigator.pop(context), child: const Text('CANCEL')),
        ElevatedButton(
          style: ElevatedButton.styleFrom(backgroundColor: Colors.purpleAccent),
          onPressed: () async {
            final content = contentController.text;
            if (content.isEmpty) return;
            Navigator.pop(context);
            setState(() => _isLoading = true);
            await _apiService.analyzeGuruStatement(selectedGuruId, content);
            _fetchData();
          }, 
          child: const Text('ANALYZE IMPACT', style: TextStyle(color: Colors.white))
        ),
      ],
    )));
  }

  Widget _buildImpactBadge(int score) {
    Color color = _getScoreColor(score);
    String label = 'NEUTRAL';
    if (score >= 70) label = 'BULLISH';
    else if (score <= 30) label = 'BEARISH';

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1), 
        borderRadius: BorderRadius.circular(20), 
        border: Border.all(color: color.withOpacity(0.3))
      ),
      child: Text('$score $label', style: TextStyle(color: color, fontWeight: FontWeight.bold, fontSize: 11)),
    );
  }

  Color _getScoreColor(int score) {
    if (score >= 70) return Colors.greenAccent;
    if (score <= 30) return Colors.redAccent;
    return Colors.grey;
  }

  BoxDecoration _glassDecoration({Color? color}) {
    return BoxDecoration(
      color: color ?? Colors.white.withOpacity(0.03),
      borderRadius: BorderRadius.circular(16),
      border: Border.all(color: Colors.white.withOpacity(0.08)),
    );
  }
}
