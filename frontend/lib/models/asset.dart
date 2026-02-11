class StockAsset {
  final int id;
  final String symbol;
  final double quantity;
  final double averagePrice;
  final DateTime updatedAt;

  StockAsset({
    required this.id,
    required this.symbol,
    required this.quantity,
    required this.averagePrice,
    required this.updatedAt,
  });

  factory StockAsset.fromJson(Map<String, dynamic> json) {
    return StockAsset(
      id: json['id'],
      symbol: json['symbol'],
      quantity: json['quantity'].toDouble(),
      averagePrice: json['average_price'].toDouble(),
      updatedAt: DateTime.parse(json['updated_at']),
    );
  }
}
