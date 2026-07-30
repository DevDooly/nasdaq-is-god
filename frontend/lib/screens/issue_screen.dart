import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../widgets/ai_header_banner.dart';
import 'package:intl/intl.dart';

class IssueScreen extends StatefulWidget {
  const IssueScreen({super.key});

  @override
  State<IssueScreen> createState() => _IssueScreenState();
}

class _IssueScreenState extends State<IssueScreen> {
  final ApiService _apiService = ApiService();
  final TextEditingController _searchController = TextEditingController();

  List<dynamic> _articles = [];
  bool _isLoading = true;
  String _selectedCategory = 'ALL'; // ALL, NEWS, GURU
  String _searchQuery = '';

  final List<Map<String, String>> _categories = [
    {'value': 'ALL', 'label': '전체'},
    {'value': 'NEWS', 'label': '📰 주식/시장 이슈 기사'},
    {'value': 'GURU', 'label': '💬 월가 대가 & 인물 발언'},
  ];

  @override
  void initState() {
    super.initState();
    _fetchIssues();
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  Future<void> _fetchIssues() async {
    setState(() => _isLoading = true);
    final res = await _apiService.getIssuesFeed(
      query: _searchQuery,
      category: _selectedCategory,
    );

    if (mounted) {
      setState(() {
        _articles = (res?['articles'] as List<dynamic>?) ?? [];
        _isLoading = false;
      });
    }
  }

  Future<void> _refreshFeed() async {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('📡 최신 뉴스 및 발언을 수집하여 DB에 보관 처리 중입니다...')),
    );
    await _apiService.refreshIssuesFeed();
    await _fetchIssues();
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
          title: const Text('🔥 실시간 이슈 & 인물 발언 피드'),
          backgroundColor: const Color(0xFF0F172A),
          actions: [
            IconButton(
              icon: const Icon(Icons.sync, color: Color(0xFF06B6D4)),
              tooltip: '최신 수집 & DB 보관',
              onPressed: _refreshFeed,
            ),
          ],
        ),
        body: Column(
          children: [
            const AiHeaderBanner(),
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // 1. DB 캐시 뱃지 & 설명
                    Container(
                      padding: const EdgeInsets.all(14),
                      decoration: BoxDecoration(
                        color: const Color(0xFF0F172A),
                        borderRadius: BorderRadius.circular(14),
                        border: Border.all(color: const Color(0xFF06B6D4).withValues(alpha: 0.3)),
                      ),
                      child: Row(
                        children: [
                          const Icon(Icons.shield_outlined, color: Color(0xFF06B6D4), size: 20),
                          const SizedBox(width: 10),
                          const Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text('⚡ DB 스마트 캐시 보관 중 (중복 호출 0건 방지)', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 13)),
                                SizedBox(height: 2),
                                Text('수집된 기사 및 대가 발언은 DB에 보관되어 재호출 시 API 차단을 완벽히 예방합니다.', style: TextStyle(color: Colors.grey, fontSize: 11)),
                              ],
                            ),
                          ),
                          ElevatedButton.icon(
                            icon: const Icon(Icons.refresh, size: 14),
                            label: const Text('동기화'),
                            style: ElevatedButton.styleFrom(
                              backgroundColor: const Color(0xFF06B6D4),
                              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                            ),
                            onPressed: _fetchIssues,
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 16),

                    // 2. 검색창 & 카테고리 필터
                    Row(
                      children: [
                        Expanded(
                          child: TextField(
                            controller: _searchController,
                            style: const TextStyle(color: Colors.white),
                            onSubmitted: (val) {
                              setState(() => _searchQuery = val);
                              _fetchIssues();
                            },
                            decoration: InputDecoration(
                              hintText: '키워드 / 인물 검색 (예: 일론 머스크, 엔비디아, 금리)',
                              hintStyle: const TextStyle(color: Colors.grey, fontSize: 13),
                              prefixIcon: const Icon(Icons.search, color: Color(0xFF06B6D4)),
                              suffixIcon: _searchController.text.isNotEmpty
                                  ? IconButton(
                                      icon: const Icon(Icons.clear, color: Colors.grey),
                                      onPressed: () {
                                        _searchController.clear();
                                        setState(() => _searchQuery = '');
                                        _fetchIssues();
                                      },
                                    )
                                  : null,
                              filled: true,
                              fillColor: const Color(0xFF1E293B),
                              border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),

                    // 카테고리 칩 선택
                    Wrap(
                      spacing: 8,
                      children: _categories.map((cat) {
                        final isSelected = _selectedCategory == cat['value'];
                        return ChoiceChip(
                          label: Text(cat['label']!),
                          selected: isSelected,
                          selectedColor: const Color(0xFF06B6D4),
                          backgroundColor: const Color(0xFF1E293B),
                          labelStyle: TextStyle(color: isSelected ? Colors.black : Colors.white, fontWeight: FontWeight.bold, fontSize: 12),
                          onSelected: (val) {
                            if (val) {
                              setState(() => _selectedCategory = cat['value']!);
                              _fetchIssues();
                            }
                          },
                        );
                      }).toList(),
                    ),
                    const SizedBox(height: 16),

                    // 3. 이슈 기사 & 발언 리스트
                    _isLoading
                        ? const Center(child: Padding(padding: EdgeInsets.all(40), child: CircularProgressIndicator(color: Color(0xFF06B6D4))))
                        : _articles.isEmpty
                            ? const Center(child: Padding(padding: EdgeInsets.all(40), child: Text('검색된 이슈 또는 인물 발언이 없습니다.', style: TextStyle(color: Colors.grey))))
                            : ListView.builder(
                                shrinkWrap: true,
                                physics: const NeverScrollableScrollPhysics(),
                                itemCount: _articles.length,
                                itemBuilder: (context, index) {
                                  final item = _articles[index];
                                  return _buildArticleCard(item);
                                },
                              ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildArticleCard(dynamic item) {
    final title = item['title'] ?? '';
    final publisher = item['publisher'] ?? 'Market';
    final summary = item['summary'] ?? '';
    final sentiment = item['sentiment'] ?? 'Neutral';
    final score = item['sentiment_score'] ?? 50;
    final category = item['category'] ?? 'NEWS';
    final pubAt = item['published_at'] != null ? DateFormat('MM-dd HH:mm').format(DateTime.parse(item['published_at'])) : '';

    Color sentColor = Colors.grey;
    if (sentiment == 'Bullish') sentColor = Colors.greenAccent;
    if (sentiment == 'Bearish') sentColor = Colors.redAccent;

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF0F172A),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white10),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: category == 'GURU' ? Colors.purple.withValues(alpha: 0.2) : Colors.blue.withValues(alpha: 0.2),
                      borderRadius: BorderRadius.circular(6),
                      border: Border.all(color: category == 'GURU' ? Colors.purpleAccent : Colors.blueAccent),
                    ),
                    child: Text(
                      category == 'GURU' ? '💬 대가 발언' : '📰 뉴스 이슈',
                      style: TextStyle(color: category == 'GURU' ? Colors.purpleAccent : Colors.blueAccent, fontWeight: FontWeight.bold, fontSize: 10),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Text(publisher, style: const TextStyle(color: Colors.white70, fontSize: 12, fontWeight: FontWeight.bold)),
                  const SizedBox(width: 8),
                  Text('· $pubAt', style: const TextStyle(color: Colors.grey, fontSize: 11)),
                ],
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                decoration: BoxDecoration(
                  color: sentColor.withValues(alpha: 0.15),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: sentColor),
                ),
                child: Text('$sentiment ($score점)', style: TextStyle(color: sentColor, fontSize: 11, fontWeight: FontWeight.bold)),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Text(title, style: const TextStyle(color: Colors.white, fontSize: 15, fontWeight: FontWeight.bold)),
          const SizedBox(height: 6),
          Text(summary, style: const TextStyle(color: Colors.white70, fontSize: 13, height: 1.4)),
          const SizedBox(height: 10),
          Row(
            mainAxisAlignment: MainAxisAlignment.end,
            children: [
              TextButton.icon(
                icon: const Icon(Icons.launch, size: 14, color: Color(0xFF06B6D4)),
                label: const Text('원문/출처 확인', style: TextStyle(color: Color(0xFF06B6D4), fontSize: 12)),
                onPressed: () {
                  final link = item['link'] ?? '';
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('🔗 원문 주소: $link')),
                  );
                },
              ),
            ],
          ),
        ],
      ),
    );
  }
}
