import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter/foundation.dart';
import 'dart:convert';
import 'dart:html' as html;
import 'package:web_socket_channel/web_socket_channel.dart';

class ApiService {
  static String get _baseUrl {
    if (kIsWeb) {
      final host = Uri.base.host;
      return 'http://$host:9000';
    }
    return 'http://localhost:9000';
  }

  static String get _wsUrl {
    if (kIsWeb) {
      final host = Uri.base.host;
      return 'ws://$host:9000/ws/updates';
    }
    return 'ws://localhost:9000/ws/updates';
  }

  final Dio _dio = Dio(BaseOptions(
    baseUrl: _baseUrl,
    connectTimeout: const Duration(seconds: 15),
    receiveTimeout: const Duration(seconds: 15),
    responseType: ResponseType.json,
  ));

  final _storage = const FlutterSecureStorage();
  static String? _backupToken;

  ApiService() {
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        String? token = await getValidToken();
        if (token != null && token.isNotEmpty) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        return handler.next(options);
      },
    ));
  }

  Future<String?> getValidToken() async {
    if (_backupToken != null) return _backupToken;
    String? token;
    if (kIsWeb) { try { token = html.window.localStorage['jwt_token']; } catch (e) {} }
    if (token == null) { try { token = await _storage.read(key: 'jwt_token'); } catch (e) {} }
    _backupToken = token;
    return token;
  }

  Future<Map<String, dynamic>?> login(String username, String password) async {
    try {
      final formData = FormData.fromMap({'username': username, 'password': password});
      final response = await _dio.post('/login', data: formData, options: Options(contentType: Headers.formUrlEncodedContentType));
      if (response.statusCode == 200 && response.data != null) {
        final token = response.data['access_token'];
        if (token != null) {
          _backupToken = token;
          if (kIsWeb) { try { html.window.localStorage['jwt_token'] = token; } catch (e) {} }
          try { await _storage.write(key: 'jwt_token', value: token); } catch (e) {}
          return response.data;
        }
      }
      return null;
    } catch (e) { return null; }
  }

  Future<void> logout() async {
    _backupToken = null;
    if (kIsWeb) { try { html.window.localStorage.remove('jwt_token'); } catch (e) {} }
    try { await _storage.delete(key: 'jwt_token'); } catch (e) {}
  }

  // 💡 실시간 업데이트 스트림 (인증 포함)
  Stream getUpdateStream() async* {
    final token = await getValidToken();
    if (token == null) return;

    try {
      final channel = WebSocketChannel.connect(Uri.parse('$_wsUrl?token=$token'));
      yield* channel.stream.map((event) => jsonDecode(event));
    } catch (e) {
      print('WebSocket Error: $e');
    }
  }

  // 💡 API 키 관리
  Future<List<dynamic>?> getApiKeys() async {
    try {
      final response = await _dio.get('/settings/api-keys');
      return response.data;
    } catch (e) { return null; }
  }

  Future<bool> addApiKey(String label, String key) async {
    try {
      final response = await _dio.post('/settings/api-keys', queryParameters: {'label': label, 'key': key});
      return response.statusCode == 200;
    } catch (e) { return false; }
  }

  Future<bool> activateApiKey(int id) async {
    try {
      final response = await _dio.patch('/settings/api-keys/$id/activate');
      return response.statusCode == 200;
    } catch (e) { return false; }
  }

  Future<bool> deleteApiKey(int id) async {
    try {
      final response = await _dio.delete('/settings/api-keys/$id');
      return response.statusCode == 200;
    } catch (e) { return false; }
  }

  // 💡 AI 서비스 관련
  Future<List<dynamic>?> getAiModels() async {
    try {
      final response = await _dio.get('/ai/models');
      return response.data;
    } catch (e) { return null; }
  }

  Future<Map<String, dynamic>?> getStockSentiment(String symbol, {String? model, bool force = false}) async {
    try {
      final response = await _dio.get('/stock/$symbol/sentiment', queryParameters: {if (model != null) 'model': model, 'force_refresh': force});
      return response.data;
    } catch (e) { return null; }
  }

  Future<Map<String, dynamic>?> getMarketSentiment() async {
    try {
      final response = await _dio.get('/market/sentiment');
      return response.data;
    } catch (e) { return null; }
  }

  // 💡 트레이딩 제어
  Future<bool> toggleMasterAutoTrading() async {
    try {
      final response = await _dio.patch('/users/me/auto-trading');
      return response.statusCode == 200;
    } catch (e) { return false; }
  }

  Future<Map<String, dynamic>?> liquidatePositions(List<String> symbols) async {
    try {
      final response = await _dio.post('/trade/liquidate', queryParameters: {'symbols': symbols});
      return response.data;
    } catch (e) { return null; }
  }

  // 💡 전략 관리
  Future<List<dynamic>?> getStrategies() async {
    try {
      final response = await _dio.get('/strategies');
      return response.data;
    } catch (e) { return null; }
  }

  Future<Map<String, dynamic>?> createStrategy(Map<String, dynamic> data) async {
    try {
      final response = await _dio.post('/strategies', data: data);
      return response.data;
    } catch (e) { return null; }
  }

  Future<bool> toggleStrategy(int id) async {
    try {
      final response = await _dio.patch('/strategies/$id/toggle');
      return response.statusCode == 200;
    } catch (e) { return false; }
  }

  Future<bool> deleteStrategy(int id) async {
    try {
      final response = await _dio.delete('/strategies/$id');
      return response.statusCode == 200;
    } catch (e) { return false; }
  }

  // 💡 시세 및 포트폴리오
  Future<Map<String, dynamic>?> getMe() async {
    try {
      final response = await _dio.get('/users/me');
      return response.data;
    } catch (e) { return null; }
  }

  Future<Map<String, dynamic>?> getPortfolio() async {
    try {
      final response = await _dio.get('/portfolio');
      return response.data;
    } catch (e) { return null; }
  }

  Future<List<dynamic>?> getPortfolioHistory() async {
    try {
      final response = await _dio.get('/portfolio/history');
      return response.data;
    } catch (e) { return null; }
  }

  Future<List<dynamic>?> getTradeHistory() async {
    try {
      final response = await _dio.get('/trade/history');
      return response.data;
    } catch (e) { return null; }
  }

  Future<Map<String, dynamic>?> getIndicators(String symbol) async {
    try {
      final response = await _dio.get('/stock/$symbol/indicators');
      return response.data;
    } catch (e) { return null; }
  }

  Future<Map<String, dynamic>?> searchStock(String query) async {
    try {
      final response = await _dio.get('/search', queryParameters: {'q': query});
      return response.data;
    } catch (e) { return null; }
  }

  Future<Map<String, dynamic>?> placeOrder(String symbol, double quantity, String side) async {
    try {
      final response = await _dio.post('/trade/order', queryParameters: {'symbol': symbol, 'quantity': quantity, 'side': side});
      return response.data;
    } catch (e) { return null; }
  }
}