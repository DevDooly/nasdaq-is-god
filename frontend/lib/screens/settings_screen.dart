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
    String selectedProvider = 'GOOGLE';
    final labelController = TextEditingController();
    final keyController = TextEditingController();
    final urlController = TextEditingController(text: 'http://localhost:11434');

    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setDState) => AlertDialog(
          backgroundColor: const Color(0xFF1E293B),
          title: const Text('AI 설정 추가', style: TextStyle(color: Colors.white)),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                DropdownButtonFormField<String>(
                  value: selectedProvider,
                  dropdownColor: const Color(0xFF1E293B),
                  style: const TextStyle(color: Colors.white),
                  decoration: const InputDecoration(labelText: 'Provider', labelStyle: TextStyle(color: Colors.grey)),
                  items: ['GOOGLE', 'OLLAMA', 'OPENAI', 'CLAUDE'].map((p) => DropdownMenuItem(value: p, child: Text(p))).toList(),
                  onChanged: (val) {
                    if (val != null) setDState(() => selectedProvider = val);
                  },
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: labelController,
                  style: const TextStyle(color: Colors.white),
                  decoration: const InputDecoration(labelText: 'Label (e.g. My PC)', labelStyle: TextStyle(color: Colors.grey)),
                ),
                if (selectedProvider == 'OLLAMA') ...[
                  const SizedBox(height: 16),
                  TextField(
                    controller: urlController,
                    style: const TextStyle(color: Colors.white),
                    decoration: const InputDecoration(labelText: 'Base URL (IP:Port)', labelStyle: TextStyle(color: Colors.grey), hintText: 'http://192.168.0.10:11434'),
                  ),
                ] else ...[
                  const SizedBox(height: 16),
                  TextField(
                    controller: keyController,
                    style: const TextStyle(color: Colors.white),
                    decoration: const InputDecoration(labelText: 'API Key', labelStyle: TextStyle(color: Colors.grey)),
                    obscureText: true,
                  ),
                ],
              ],
            ),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(context), child: const Text('취소')),
            ElevatedButton(
              onPressed: () async {
                final data = {
                  'provider': selectedProvider,
                  'label': labelController.text,
                  'key': keyController.text,
                  'base_url': selectedProvider == 'OLLAMA' ? urlController.text : null,
                };
                final success = await _apiService.addApiKeyFromMap(data);
                if (success && mounted) {
                  Navigator.pop(context);
                  _fetchKeys();
                }
              },
              child: const Text('저장'),
            )
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('AI CONFIGURATION')),
      backgroundColor: const Color(0xFF0F172A),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: Colors.cyanAccent))
          : Padding(
              padding: const EdgeInsets.all(24.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('AI PROVIDERS', style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Colors.white, letterSpacing: 1)),
                  const SizedBox(height: 8),
                  const Text(
                    '여러 AI 프로바이더를 등록하고 관리할 수 있습니다. 활성화된 프로바이더가 분석에 사용됩니다.',
                    style: TextStyle(color: Colors.grey, fontSize: 13),
                  ),
                  const SizedBox(height: 32),
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
        label: const Text('ADD CONFIG'),
        backgroundColor: Colors.blueAccent,
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.psychology_outlined, size: 64, color: Colors.grey[800]),
          const SizedBox(height: 16),
          const Text('등록된 AI 설정이 없습니다.', style: TextStyle(color: Colors.grey)),
        ],
      ),
    );
  }

  Widget _buildKeyCard(dynamic key) {
    final bool isActive = key['is_active'] ?? false;
    final provider = key['provider'] ?? 'GOOGLE';
    final lastUsed = key['last_used_at'] != null 
        ? DateFormat('MM/dd HH:mm').format(DateTime.parse(key['last_used_at']))
        : 'Never';

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: isActive ? Colors.blueAccent.withOpacity(0.1) : Colors.white.withOpacity(0.02),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: isActive ? Colors.blueAccent : Colors.white.withOpacity(0.05)),
      ),
      child: Row(
        children: [
          _getProviderIcon(provider),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Text(key['label'], style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: Colors.white)),
                    const SizedBox(width: 8),
                    _buildProviderBadge(provider),
                    if (isActive) ...[
                      const SizedBox(width: 8),
                      const Icon(Icons.bolt, color: Colors.amberAccent, size: 16),
                    ]
                  ],
                ),
                const SizedBox(height: 6),
                if (provider == 'OLLAMA')
                  Text('URL: ${key['base_url']}', style: const TextStyle(color: Colors.grey, fontSize: 11, fontFamily: 'monospace'))
                else
                  Text('Key: ${key['key_value']}', style: const TextStyle(color: Colors.grey, fontSize: 11, fontFamily: 'monospace')),
                const SizedBox(height: 12),
                Row(
                  children: [
                    _buildInfoBadge(Icons.analytics_outlined, '${key['usage_count']} uses'),
                    const SizedBox(width: 16),
                    _buildInfoBadge(Icons.access_time, 'Last: $lastUsed'),
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
              ),
            ],
          )
        ],
      ),
    );
  }

  Widget _getProviderIcon(String provider) {
    IconData icon = Icons.api;
    Color color = Colors.grey;
    if (provider == 'GOOGLE') { icon = Icons.bubble_chart; color = Colors.blue; }
    if (provider == 'OLLAMA') { icon = Icons.storage; color = Colors.orange; }
    if (provider == 'OPENAI') { icon = Icons.bolt; color = Colors.green; }
    if (provider == 'CLAUDE') { icon = Icons.auto_awesome; color = Colors.purple; }
    return Icon(icon, color: color, size: 32);
  }

  Widget _buildProviderBadge(String p) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(color: Colors.white10, borderRadius: BorderRadius.circular(4)),
      child: Text(p, style: const TextStyle(fontSize: 9, fontWeight: FontWeight.bold, color: Colors.grey)),
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
        title: const Text('설정을 삭제하시겠습니까?'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('취소')),
          TextButton(onPressed: () => Navigator.pop(context, true), child: const Text('삭제', style: TextStyle(color: Colors.redAccent))),
        ],
      ),
    );
  }
}
