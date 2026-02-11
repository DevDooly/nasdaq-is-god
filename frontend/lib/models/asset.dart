class StockAsset {
  final int id;
  final String symbol;
  final double quantity;
  final double averagePrice;
  final double currentPrice;
  final double profit;
  final double profitRate;
  final DateTime updatedAt;

  StockAsset({
    required this.id,
    required this.symbol,
    required this.quantity,
    required this.averagePrice,
    required this.currentPrice,
    required this.profit,
    required this.profitRate,
    required this.updatedAt,
  });

  factory StockAsset.fromJson(Map<String, dynamic> json) {
    return StockAsset(
      id: json['id'],
      symbol: json['symbol'],
      quantity: json['quantity'].toDouble(),
      averagePrice: json['average_price'].toDouble(),
      currentPrice: (json['current_price'] ?? json['average_price']).toDouble(),
      profit: (json['profit'] ?? 0.0).toDouble(),
      profitRate: (json['profit_rate'] ?? 0.0).toDouble(),
      updatedAt: DateTime.parse(json['updated_at']),
    );
  }
}