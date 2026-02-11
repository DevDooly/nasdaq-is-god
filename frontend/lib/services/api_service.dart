import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter/foundation.dart';
import 'dart:convert';
import 'dart:html' as html;

class ApiService {
  static String get _baseUrl {
    if (kIsWeb) {
      final host = Uri.base.host;
      return 'http://$host:9000';
    }
    return 'http://localhost:9000';
  }

  final Dio _dio = Dio(BaseOptions(
    baseUrl: _baseUrl,
    connectTimeout: const Duration(seconds: 15),
    receiveTimeout: const Duration(seconds: 15),
  ));

  final _storage = const FlutterSecureStorage();
  
  static String? _backupToken;

  ApiService() {
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        String? token = _backupToken;
        if (token == null && kIsWeb) {
          token = html.window.localStorage['jwt_token'];
        }
        if (token == null) {
          try {
            token = await _storage.read(key: 'jwt_token');
          } catch (e) {}
        }

        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        return handler.next(options);
      },
    ));
  }

  Future<Map<String, dynamic>?> login(String username, String password) async {
    try {
      final formData = FormData.fromMap({'username': username, 'password': password});
      final response = await _dio.post('/login', data: formData, options: Options(contentType: Headers.formUrlEncodedContentType));
      
      if (response.statusCode == 200 && response.data != null) {
        final token = response.data['access_token'];
        if (token != null) {
          _backupToken = token;
          if (kIsWeb) html.window.localStorage['jwt_token'] = token;
          await _storage.write(key: 'jwt_token', value: token);
          return response.data;
        }
      }
      return null;
    } catch (e) {
      return null;
    }
  }

  Future<Map<String, dynamic>?> getMe() async {
    try {
      final response = await _dio.get('/users/me');
      return response.data;
    } catch (e) {
      return null;
    }
  }

  Future<List<dynamic>?> getPortfolio() async {
    try {
      final response = await _dio.get('/portfolio');
      return response.data;
    } catch (e) {
      return null;
    }
  }

  Future<List<dynamic>?> getTradeHistory() async {
    try {
      final response = await _dio.get('/trade/history');
      return response.data;
    } catch (e) {
      return null;
    }
  }

  Future<Map<String, dynamic>?> getIndicators(String symbol) async {
    try {
      final response = await _dio.get('/stock/$symbol/indicators');
      return response.data;
    } catch (e) {
      return null;
    }
  }

  Future<Map<String, dynamic>?> searchStock(String query) async {
    try {
      final response = await _dio.get('/search', queryParameters: {'q': query});
      return response.data;
    } catch (e) {
      return null;
    }
  }

  Future<Map<String, dynamic>?> placeOrder(String symbol, double quantity, String side) async {
    try {
      final response = await _dio.post('/trade/order', queryParameters: {'symbol': symbol, 'quantity': quantity, 'side': side});
      return response.data;
    } catch (e) {
      return null;
    }
  }
}