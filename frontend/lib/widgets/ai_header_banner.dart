import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../screens/settings_screen.dart';

class AiHeaderBanner extends StatefulWidget {
  const AiHeaderBanner({super.key});

  @override
  State<AiHeaderBanner> createState() => _AiHeaderBannerState();
}

class _AiHeaderBannerState extends State<AiHeaderBanner> {
  final ApiService _apiService = ApiService();
  Map<String, dynamic>? _aiStatus;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _fetchAiStatus();
  }

  Future<void> _fetchAiStatus() async {
    final status = await _apiService.getActiveAiStatus();
    if (mounted) {
      setState(() {
        _aiStatus = status;
        _isLoading = false;
      });
    }
  }

  void _showQuickSwitchModal() async {
    final keys = await _apiService.getApiKeys();
    if (!mounted) return;

    showModalBottomSheet(
      context: context,
      backgroundColor: const Color(0xFF1E293B),
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (context) {
        return Container(
          padding: const EdgeInsets.all(20),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text('⚡ AI 프로바이더 / API 즉시 전환', style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold)),
                  Icon(Icons.swap_horiz, color: Color(0xFF06B6D4)),
                ],
              ),
              const SizedBox(height: 12),
              if (keys == null || keys.isEmpty)
                const Padding(
                  padding: EdgeInsets.symmetric(vertical: 20),
                  child: Text('등록된 사용자 API 키가 없습니다. 기본 ENV 설정이 사용 중입니다.', style: TextStyle(color: Colors.grey)),
                )
              else
                ListView.builder(
                  shrinkWrap: true,
                  itemCount: keys.length,
                  itemBuilder: (context, index) {
                    final item = keys[index];
                    final isActive = item['is_active'] == true;
                    return ListTile(
                      dense: true,
                      leading: Icon(
                        item['provider'] == 'GOOGLE' ? Icons.auto_awesome : Icons.computer,
                        color: isActive ? const Color(0xFF06B6D4) : Colors.grey,
                      ),
                      title: Text('${item['provider']} · ${item['label'] ?? ""}', style: TextStyle(color: isActive ? const Color(0xFF06B6D4) : Colors.white, fontWeight: FontWeight.bold)),
                      subtitle: Text(item['key_value'] ?? item['base_url'] ?? '', style: const TextStyle(color: Colors.grey, fontSize: 11)),
                      trailing: isActive
                          ? const Chip(label: Text('활성', style: TextStyle(fontSize: 10, color: Colors.black)), backgroundColor: Color(0xFF06B6D4))
                          : ElevatedButton(
                              style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF334155)),
                              onPressed: () async {
                                await _apiService.activateApiKey(item['id']);
                                if (context.mounted) Navigator.pop(context);
                                _fetchAiStatus();
                              },
                              child: const Text('선택', style: TextStyle(fontSize: 12)),
                            ),
                    );
                  },
                ),
              const SizedBox(height: 12),
              SizedBox(
                width: double.infinity,
                child: OutlinedButton.icon(
                  icon: const Icon(Icons.add, size: 16),
                  label: const Text('신규 API 키 추가 / 관리 페이지 이동'),
                  style: OutlinedButton.styleFrom(foregroundColor: const Color(0xFF06B6D4)),
                  onPressed: () {
                    Navigator.pop(context);
                    Navigator.push(context, MaterialPageRoute(builder: (context) => const SettingsScreen()));
                  },
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  void _showDetailModal() {
    if (_aiStatus == null) return;
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: const Color(0xFF1E293B),
        title: const Text('🤖 AI 서비스 상세 정보', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _detailRow('제조사 / 플랫폼', _aiStatus!['vendor_name'] ?? 'N/A'),
            _detailRow('사용 중인 모델', _aiStatus!['model_name'] ?? 'N/A'),
            _detailRow('프로바이더 구분', _aiStatus!['provider'] ?? 'N/A'),
            _detailRow('설정 라벨', _aiStatus!['label'] ?? 'N/A'),
            _detailRow('마스킹 키 / 주소', _aiStatus!['masked_key'] ?? 'N/A'),
            _detailRow('연결 상태', _aiStatus!['status'] ?? 'N/A'),
            _detailRow('일일 토큰 / 할당량', _aiStatus!['quota_status'] ?? 'N/A'),
            _detailRow('추정 잔여율', _aiStatus!['remaining_estimate'] ?? 'N/A'),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('닫기')),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF06B6D4)),
            onPressed: () {
              Navigator.pop(context);
              _showQuickSwitchModal();
            },
            child: const Text('API 변경'),
          ),
        ],
      ),
    );
  }

  Widget _detailRow(String label, String val) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(color: Colors.grey, fontSize: 13)),
          Text(val, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 13)),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return Container(
        height: 36,
        color: const Color(0xFF0B1329),
        child: const Center(child: SizedBox(width: 14, height: 14, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.grey))),
      );
    }

    final status = _aiStatus ?? {};
    final isHealthy = status['healthy'] == true;
    final vendor = status['vendor_name'] ?? 'AI Engine';
    final model = status['model_name'] ?? 'Gemini';
    final quota = status['quota_status'] ?? 'Free Tier';
    final remaining = status['remaining_estimate'] ?? '100%';

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: const BoxDecoration(
        color: Color(0xFF090D16),
        border: Border(bottom: BorderSide(color: Colors.white10)),
      ),
      child: Row(
        children: [
          // 상태 라이트 애니메이션
          Container(
            width: 8,
            height: 8,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: isHealthy ? const Color(0xFF10B981) : Colors.redAccent,
              boxShadow: [
                BoxShadow(
                  color: (isHealthy ? const Color(0xFF10B981) : Colors.redAccent).withValues(alpha: 0.6),
                  blurRadius: 6,
                )
              ],
            ),
          ),
          const SizedBox(width: 10),

          // VENDOR & MODEL 뱃지
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
            decoration: BoxDecoration(
              color: const Color(0xFF06B6D4).withValues(alpha: 0.15),
              borderRadius: BorderRadius.circular(6),
              border: Border.all(color: const Color(0xFF06B6D4).withValues(alpha: 0.4)),
            ),
            child: Text(
              '[$vendor] $model',
              style: const TextStyle(color: Color(0xFF06B6D4), fontSize: 11, fontWeight: FontWeight.bold),
            ),
          ),
          const SizedBox(width: 10),

          // 토큰 / 할당량 정보
          Expanded(
            child: Text(
              '토큰/할당량: $quota (잔여 $remaining)',
              style: const TextStyle(color: Colors.white70, fontSize: 11),
              overflow: TextOverflow.ellipsis,
            ),
          ),

          // 액션 버튼들
          InkWell(
            onTap: _showQuickSwitchModal,
            child: const Padding(
              padding: EdgeInsets.symmetric(horizontal: 6, vertical: 2),
              child: Row(
                children: [
                  Icon(Icons.swap_horiz, color: Color(0xFF3B82F6), size: 14),
                  SizedBox(width: 4),
                  Text('API 전환', style: TextStyle(color: Color(0xFF3B82F6), fontSize: 11, fontWeight: FontWeight.bold)),
                ],
              ),
            ),
          ),
          const SizedBox(width: 8),
          InkWell(
            onTap: _showDetailModal,
            child: const Padding(
              padding: EdgeInsets.symmetric(horizontal: 6, vertical: 2),
              child: Row(
                children: [
                  Icon(Icons.info_outline, color: Colors.grey, size: 14),
                  SizedBox(width: 4),
                  Text('상세', style: TextStyle(color: Colors.grey, fontSize: 11)),
                ],
              ),
            ),
          ),
          const SizedBox(width: 6),
          IconButton(
            icon: const Icon(Icons.refresh, color: Colors.grey, size: 14),
            padding: EdgeInsets.zero,
            constraints: const BoxConstraints(),
            onPressed: () {
              setState(() => _isLoading = true);
              _fetchAiStatus();
            },
          ),
        ],
      ),
    );
  }
}
