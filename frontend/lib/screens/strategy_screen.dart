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
        title: const Text('Add RSI Strategy', style: TextStyle(color: Colors.white)),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(controller: nameController, style: const TextStyle(color: Colors.white), decoration: const InputDecoration(labelText: 'Strategy Name', labelStyle: TextStyle(color: Colors.grey))),
              TextField(controller: symbolController, style: const TextStyle(color: Colors.white), decoration: const InputDecoration(labelText: 'Symbol (e.g. TSLA)', labelStyle: TextStyle(color: Colors.grey))),
              TextField(controller: buyRsiController, keyboardType: TextInputType.number, style: const TextStyle(color: Colors.white), decoration: const InputDecoration(labelText: 'Buy RSI Threshold', labelStyle: TextStyle(color: Colors.grey))),
              TextField(controller: sellRsiController, keyboardType: TextInputType.number, style: const TextStyle(color: Colors.white), decoration: const InputDecoration(labelText: 'Sell RSI Threshold', labelStyle: TextStyle(color: Colors.grey))),
            ],
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
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
            child: const Text('Add'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Auto Trading Strategies')),
      backgroundColor: const Color(0xFF0F172A),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _strategies == null || _strategies!.isEmpty
              ? const Center(child: Text('No strategies found', style: TextStyle(color: Colors.grey)))
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
                              title: const Text('Delete Strategy?'),
                              actions: [
                                TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('No')),
                                TextButton(onPressed: () => Navigator.pop(context, true), child: const Text('Yes')),
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