class TradeLog {
  final int id;
  final String symbol;
  final String side;
  final double quantity;
  final double price;
  final double totalAmount;
  final DateTime executedAt;

  TradeLog({
    required this.id,
    required this.symbol,
    required this.side,
    required this.quantity,
    required this.price,
    required this.totalAmount,
    required this.executedAt,
  });

  factory TradeLog.fromJson(Map<String, dynamic> json) {
    return TradeLog(
      id: json['id'],
      symbol: json['symbol'],
      side: json['side'],
      quantity: json['quantity'].toDouble(),
      price: json['price'].toDouble(),
      totalAmount: json['total_amount'].toDouble(),
      executedAt: DateTime.parse(json['executed_at']),
    );
  }
}
