class TradingStrategy {
  final int id;
  final String name;
  final String symbol;
  final bool isActive;
  final String strategyType;
  final String parameters;
  final DateTime createdAt;

  TradingStrategy({
    required this.id,
    required this.name,
    required this.symbol,
    required this.isActive,
    required this.strategyType,
    required this.parameters,
    required this.createdAt,
  });

  factory TradingStrategy.fromJson(Map<String, dynamic> json) {
    return TradingStrategy(
      id: json['id'],
      name: json['name'],
      symbol: json['symbol'],
      isActive: json['is_active'],
      strategyType: json['strategy_type'],
      parameters: json['parameters'],
      createdAt: DateTime.parse(json['created_at']),
    );
  }
}
