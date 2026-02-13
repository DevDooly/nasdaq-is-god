import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/strategy.dart';
import 'dart:convert';

class StrategyScreen extends StatefulWidget {
  const StrategyScreen({super.key});

  @override
  State<StrategyScreen> createState() => _StrategyScreenState();
}

class _StrategyScreenState extends State<StrategyScreen> {
  final ApiService _apiService = ApiService();
  List<TradingStrategy>? _strategies;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _fetchStrategies();
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

  void _showAddStrategyDialog() {
    final nameController = TextEditingController();
    final symbolController = TextEditingController();
    final buyRsiController = TextEditingController(text: '30');
    final sellRsiController = TextEditingController(text: '70');

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: const Color(0xFF1E293B),
        title: const Text('RSI 전략 추가', style: TextStyle(color: Colors.white)),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(controller: nameController, style: const TextStyle(color: Colors.white), decoration: const InputDecoration(labelText: '전략 이름', labelStyle: TextStyle(color: Colors.grey))),
              TextField(controller: symbolController, style: const TextStyle(color: Colors.white), decoration: const InputDecoration(labelText: '티커 (예: TSLA)', labelStyle: TextStyle(color: Colors.grey))),
              TextField(controller: buyRsiController, keyboardType: TextInputType.number, style: const TextStyle(color: Colors.white), decoration: const InputDecoration(labelText: '매수 RSI 기준값', labelStyle: TextStyle(color: Colors.grey))),
              TextField(controller: sellRsiController, keyboardType: TextInputType.number, style: const TextStyle(color: Colors.white), decoration: const InputDecoration(labelText: '매도 RSI 기준값', labelStyle: TextStyle(color: Colors.grey))),
            ],
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('취소')),
          ElevatedButton(
            onPressed: () async {
              final params = {
                "buy_rsi": int.tryParse(buyRsiController.text) ?? 30,
                "sell_rsi": int.tryParse(sellRsiController.text) ?? 70,
              };
              await _apiService.createStrategy({
                "name": nameController.text,
                "symbol": symbolController.text.toUpperCase(),
                "strategy_type": "RSI_LIMIT",
                "parameters": jsonEncode(params),
                "is_active": false,
              });
              Navigator.pop(context);
              _fetchStrategies();
            },
            child: const Text('추가'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('자동 매매 전략')),
      backgroundColor: const Color(0xFF0F172A),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _strategies == null || _strategies!.isEmpty
               ? const Center(child: Text('등록된 전략이 없습니다', style: TextStyle(color: Colors.grey)))
              : ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: _strategies!.length,
                  itemBuilder: (context, index) {
                    final strategy = _strategies![index];
                    return Card(
                      color: Colors.white.withOpacity(0.05),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      child: ListTile(
                        title: Text(strategy.name, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                        subtitle: Text('${strategy.symbol} · ${strategy.strategyType}', style: const TextStyle(color: Colors.grey)),
                        trailing: Switch(
                          value: strategy.isActive,
                          onChanged: (val) async {
                            await _apiService.toggleStrategy(strategy.id);
                            _fetchStrategies();
                          },
                        ),
                        onLongPress: () async {
                          final confirm = await showDialog<bool>(
                            context: context,
                            builder: (context) => AlertDialog(
                              title: const Text('전략을 삭제하시겠습니까?'),
                              actions: [
                                TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('아니오')),
                                TextButton(onPressed: () => Navigator.pop(context, true), child: const Text('예')),
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
                ),
      floatingActionButton: FloatingActionButton(
        onPressed: _showAddStrategyDialog,
        child: const Icon(Icons.add),
      ),
    );
  }
}