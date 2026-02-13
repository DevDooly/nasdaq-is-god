import 'package:flutter/material.dart';
import '../services/api_service.dart';
import 'package:intl/intl.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  final ApiService _apiService = ApiService();
  List<dynamic>? _apiKeys;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _fetchKeys();
  }

  Future<void> _fetchKeys() async {
    setState(() => _isLoading = true);
    final keys = await _apiService.getApiKeys();
    if (mounted) {
      setState(() {
        _apiKeys = keys;
        _isLoading = false;
      });
    }
  }

  void _showAddKeyDialog() {
    final labelController = TextEditingController();
    final keyController = TextEditingController();

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: const Color(0xFF1E293B),
        title: const Text('Gemini API 키 추가', style: TextStyle(color: Colors.white)),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: labelController,
              style: const TextStyle(color: Colors.white),
              decoration: const InputDecoration(labelText: '라벨 (예: 키 1)', labelStyle: TextStyle(color: Colors.grey)),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: keyController,
              style: const TextStyle(color: Colors.white),
              decoration: const InputDecoration(labelText: 'API Key', labelStyle: TextStyle(color: Colors.grey)),
              obscureText: true,
            ),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('취소')),
          ElevatedButton(
            onPressed: () async {
              if (labelController.text.isNotEmpty && keyController.text.isNotEmpty) {
                final success = await _apiService.addApiKey(labelController.text, keyController.text);
                if (success && mounted) {
                  Navigator.pop(context);
                  _fetchKeys();
                }
              }
            },
            child: const Text('키 추가'),
          )
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('설정')),
      backgroundColor: const Color(0xFF0F172A),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('AI API 키 관리', style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Colors.white)),
                  const SizedBox(height: 8),
                  const Text(
                    '할당량 제한을 피하기 위해 여러 키를 등록할 수 있습니다. 활성화된 키가 모든 AI 분석에 사용됩니다.',
                    style: TextStyle(color: Colors.grey, fontSize: 13),
                  ),
                  const SizedBox(height: 24),
                  Expanded(
                    child: _apiKeys == null || _apiKeys!.isEmpty
                        ? _buildEmptyState()
                        : ListView.separated(
                            itemCount: _apiKeys!.length,
                            separatorBuilder: (context, index) => const SizedBox(height: 12),
                            itemBuilder: (context, index) {
                              final key = _apiKeys![index];
                              return _buildKeyCard(key);
                            },
                          ),
                  ),
                ],
              ),
            ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _showAddKeyDialog,
        icon: const Icon(Icons.add),
        label: const Text('새 키 추가'),
        backgroundColor: Colors.blueAccent,
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.vpn_key_outlined, size: 64, color: Colors.grey[700]),
          const SizedBox(height: 16),
          const Text('등록된 API 키가 없습니다.', style: TextStyle(color: Colors.grey)),
        ],
      ),
    );
  }

  Widget _buildKeyCard(dynamic key) {
    final bool isActive = key['is_active'] ?? false;
    final lastUsed = key['last_used_at'] != null 
        ? DateFormat('MM/dd HH:mm').format(DateTime.parse(key['last_used_at']))
        : '기록 없음';

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: isActive ? Colors.blueAccent.withOpacity(0.1) : Colors.white.withOpacity(0.03),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: isActive ? Colors.blueAccent : Colors.white10),
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Text(key['label'], style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: Colors.white)),
                    if (isActive) ...[
                      const SizedBox(width: 8),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(color: Colors.blueAccent, borderRadius: BorderRadius.circular(4)),
                        child: const Text('활성', style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold)),
                      )
                    ]
                  ],
                ),
                const SizedBox(height: 4),
                Text('Key: ${key['key_value']}', style: const TextStyle(color: Colors.grey, fontSize: 12, fontFamily: 'monospace')),
                const SizedBox(height: 8),
                Row(
                  children: [
                    _buildInfoBadge(Icons.analytics_outlined, '사용: ${key['usage_count']}회'),
                    const SizedBox(width: 12),
                    _buildInfoBadge(Icons.access_time, '최근: $lastUsed'),
                  ],
                )
              ],
            ),
          ),
          Column(
            children: [
              if (!isActive)
                IconButton(
                  icon: const Icon(Icons.check_circle_outline, color: Colors.greenAccent),
                  onPressed: () async {
                    await _apiService.activateApiKey(key['id']);
                    _fetchKeys();
                  },
                  tooltip: 'Activate',
                ),
              IconButton(
                icon: const Icon(Icons.delete_outline, color: Colors.redAccent),
                onPressed: () async {
                  final confirm = await _showDeleteConfirm();
                  if (confirm == true) {
                    await _apiService.deleteApiKey(key['id']);
                    _fetchKeys();
                  }
                },
                tooltip: 'Delete',
              ),
            ],
          )
        ],
      ),
    );
  }

  Widget _buildInfoBadge(IconData icon, String text) {
    return Row(
      children: [
        Icon(icon, size: 12, color: Colors.grey),
        const SizedBox(width: 4),
        Text(text, style: const TextStyle(color: Colors.grey, fontSize: 11)),
      ],
    );
  }

  Future<bool?> _showDeleteConfirm() {
    return showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: const Color(0xFF1E293B),
        title: const Text('API 키를 삭제하시겠습니까?'),
        content: const Text('이 작업은 되돌릴 수 없습니다.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('취소')),
          TextButton(onPressed: () => Navigator.pop(context, true), child: const Text('삭제', style: TextStyle(color: Colors.redAccent))),
        ],
      ),
    );
  }
}
