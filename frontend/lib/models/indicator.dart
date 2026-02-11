class IndicatorData {
  final String symbol;
  final double price;
  final double? rsi;
  final MacdData macd;
  final BollingerData bollinger;
  final List<ChartPoint> history;
  final String timestamp;

  IndicatorData({
    required this.symbol,
    required this.price,
    this.rsi,
    required this.macd,
    required this.bollinger,
    required this.history,
    required this.timestamp,
  });

  factory IndicatorData.fromJson(Map<String, dynamic> json) {
    var historyList = json['history'] as List;
    return IndicatorData(
      symbol: json['symbol'],
      price: (json['current_price'] ?? json['price']).toDouble(),
      rsi: json['rsi']?.toDouble(),
      macd: MacdData.fromJson(json['macd']),
      bollinger: BollingerData.fromJson(json['bollinger']),
      history: historyList.map((i) => ChartPoint.fromJson(i)).toList(),
      timestamp: json['timestamp'],
    );
  }
}

class ChartPoint {
  final String date;
  final double price;
  final double? rsi;
  final double? macd;
  final double? macdHist;

  ChartPoint({
    required this.date,
    required this.price,
    this.rsi,
    this.macd,
    this.macdHist,
  });

  factory ChartPoint.fromJson(Map<String, dynamic> json) {
    return ChartPoint(
      date: json['date'],
      price: json['price'].toDouble(),
      rsi: json['rsi']?.toDouble(),
      macd: json['macd']?.toDouble(),
      macdHist: json['macd_hist']?.toDouble(),
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