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
    responseType: ResponseType.json,
  ));

  final _storage = const FlutterSecureStorage();
  
  // 💡 저장소가 막혔을 때를 대비한 메모리 백업
  static String? _backupToken;

  ApiService() {
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        String? token = _backupToken;
        
        // 메모리에 없으면 저장소 시도
        if (token == null) {
          if (kIsWeb) {
            try { token = html.window.localStorage['jwt_token']; } catch (e) {}
          }
          if (token == null) {
            try { token = await _storage.read(key: 'jwt_token'); } catch (e) {}
          }
        }

        if (token != null && token.isNotEmpty) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        return handler.next(options);
      },
    ));
  }

  // 로그인 (가장 확실한 전송 방식 적용)
  Future<Map<String, dynamic>?> login(String username, String password) async {
    try {
      print('🔑 [API] Attempting login for: $username');
      
      // FastAPI OAuth2PasswordRequestForm expects x-www-form-urlencoded
      // Dio sends this correctly when data is a Map and contentType is set
      final response = await _dio.post(
        '/login',
        data: {
          'username': username,
          'password': password,
        },
        options: Options(
          contentType: Headers.formUrlEncodedContentType,
        ),
      );
      
      if (response.statusCode == 200 && response.data != null) {
        final data = response.data;
        final token = data['access_token'];
        
        if (token != null) {
          _backupToken = token; // 메모리 우선 저장
          if (kIsWeb) {
            try { html.window.localStorage['jwt_token'] = token; } catch (e) {}
          }
          try { await _storage.write(key: 'jwt_token', value: token); } catch (e) {}
          
          print('✅ [API] Login Successful and token cached');
          return data;
        }
      }
      return null;
    } catch (e) {
      print('🚨 [API] Login Crash: $e');
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
      final response = await _dio.post(
        '/trade/order', 
        queryParameters: {
          'symbol': symbol,
          'quantity': quantity,
          'side': side,
        }
      );
      return response.data;
    } catch (e) {
      return null;
    }
  }

  Future<List<dynamic>?> getStrategies() async {
    try {
      final response = await _dio.get('/strategies');
      return response.data;
    } catch (e) {
      return null;
    }
  }

  Future<Map<String, dynamic>?> createStrategy(Map<String, dynamic> data) async {
    try {
      final response = await _dio.post('/strategies', data: data);
      return response.data;
    } catch (e) {
      return null;
    }
  }

  Future<bool> toggleStrategy(int id) async {
    try {
      final response = await _dio.patch('/strategies/$id/toggle');
      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }

  Future<bool> deleteStrategy(int id) async {
    try {
      final response = await _dio.delete('/strategies/$id');
      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }
}
