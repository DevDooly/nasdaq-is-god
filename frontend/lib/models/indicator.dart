class IndicatorData {
  final String symbol;
  final double price;
  final double? rsi;
  final MacdData macd;
  final BollingerData bollinger;
  final String timestamp;

  IndicatorData({
    required this.symbol,
    required this.price,
    this.rsi,
    required this.macd,
    required this.bollinger,
    required this.timestamp,
  });

  factory IndicatorData.fromJson(Map<String, dynamic> json) {
    return IndicatorData(
      symbol: json['symbol'],
      price: json['price'].toDouble(),
      rsi: json['rsi']?.toDouble(),
      macd: MacdData.fromJson(json['macd']),
      bollinger: BollingerData.fromJson(json['bollinger']),
      timestamp: json['timestamp'],
    );
  }
}

class MacdData {
  final double val;
  final double signal;
  final double hist;

  MacdData({required this.val, required this.signal, required this.hist});

  factory MacdData.fromJson(Map<String, dynamic> json) {
    return MacdData(
      val: json['val'].toDouble(),
      signal: json['signal'].toDouble(),
      hist: json['hist'].toDouble(),
    );
  }
}

class BollingerData {
  final double upper;
  final double middle;
  final double lower;

  BollingerData({required this.upper, required this.middle, required this.lower});

  factory BollingerData.fromJson(Map<String, dynamic> json) {
    return BollingerData(
      upper: json['upper'].toDouble(),
      middle: json['middle'].toDouble(),
      lower: json['lower'].toDouble(),
    );
  }
}
