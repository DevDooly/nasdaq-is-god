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
        title: const Text('Add Gemini API Key', style: TextStyle(color: Colors.white)),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: labelController,
              style: const TextStyle(color: Colors.white),
              decoration: const InputDecoration(labelText: 'Label (e.g. My Key 1)', labelStyle: TextStyle(color: Colors.grey)),
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
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
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
            child: const Text('Add Key'),
          )
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Settings')),
      backgroundColor: const Color(0xFF0F172A),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('AI API Key Management', style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Colors.white)),
                  const SizedBox(height: 8),
                  const Text(
                    'Register multiple keys to avoid quota limits. The active key will be used for all AI analysis.',
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
        label: const Text('Add New Key'),
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
          const Text('No API keys registered yet.', style: TextStyle(color: Colors.grey)),
        ],
      ),
    );
  }

  Widget _buildKeyCard(dynamic key) {
    final bool isActive = key['is_active'] ?? false;
    final lastUsed = key['last_used_at'] != null 
        ? DateFormat('MM/dd HH:mm').format(DateTime.parse(key['last_used_at']))
        : 'Never';

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
                        child: const Text('ACTIVE', style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold)),
                      )
                    ]
                  ],
                ),
                const SizedBox(height: 4),
                Text('Key: ${key['key_value']}', style: const TextStyle(color: Colors.grey, fontSize: 12, fontFamily: 'monospace')),
                const SizedBox(height: 8),
                Row(
                  children: [
                    _buildInfoBadge(Icons.analytics_outlined, 'Used: ${key['usage_count']}'),
                    const SizedBox(width: 12),
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
        title: const Text('Delete API Key?'),
        content: const Text('This action cannot be undone.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancel')),
          TextButton(onPressed: () => Navigator.pop(context, true), child: const Text('Delete', style: TextStyle(color: Colors.redAccent))),
        ],
      ),
    );
  }
}
