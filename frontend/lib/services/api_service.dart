import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter/foundation.dart';
import 'dart:convert';

class ApiService {
  static String get _baseUrl {
    if (kIsWeb) {
      final uri = Uri.base;
      return 'http://${uri.host}:9000';
    }
    return 'http://localhost:9000';
  }

  final Dio _dio = Dio(BaseOptions(
    baseUrl: _baseUrl,
    connectTimeout: const Duration(seconds: 15),
    receiveTimeout: const Duration(seconds: 15),
  ));

  // 웹 환경 호환성 설정 (파라미터 오류 수정)
  final _storage = const FlutterSecureStorage();

  ApiService() {
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        try {
          // 💡 매 요청마다 저장소에서 토큰을 읽어 헤더에 부착
          final token = await _storage.read(key: 'jwt_token');
          if (token != null && token.isNotEmpty) {
            options.headers['Authorization'] = 'Bearer $token';
            print('🔑 [Auth] Token attached to: ${options.path}');
          } else {
            print('⚠️ [Auth] No token found for: ${options.path}');
          }
        } catch (e) {
          print('🚨 [Auth Error] $e');
        }
        return handler.next(options);
      },
      onError: (DioException e, handler) {
        if (e.response?.statusCode == 401) {
          print('❌ [Auth Error] 401 Unauthorized - 로그인 세션 만료 가능성');
        }
        return handler.next(e);
      },
    ));
  }

  // 로그인
  Future<Map<String, dynamic>?> login(String username, String password) async {
    try {
      print('🔑 [Login] Attempting for $username');
      
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
      
      dynamic data = response.data;
      if (data is String) data = jsonDecode(data);

      if (response.statusCode == 200 && data != null) {
        final token = data['access_token'];
        if (token != null) {
          await _storage.write(key: 'jwt_token', value: token);
          print('✅ [Login] Success');
          return data;
        }
      }
      return null;
    } catch (e) {
      print('🚨 [Login Error] $e');
      return null;
    }
  }

  Future<Map<String, dynamic>?> getMe() async {
    try {
      final response = await _dio.get('/users/me');
      dynamic data = response.data;
      return data is String ? jsonDecode(data) : data;
    } catch (e) {
      return null;
    }
  }

  Future<List<dynamic>?> getPortfolio() async {
    try {
      final response = await _dio.get('/portfolio');
      dynamic data = response.data;
      return data is String ? jsonDecode(data) : data;
    } catch (e) {
      return null;
    }
  }

  Future<Map<String, dynamic>?> getIndicators(String symbol) async {
    try {
      final response = await _dio.get('/stock/$symbol/indicators');
      dynamic data = response.data;
      return data is String ? jsonDecode(data) : data;
    } catch (e) {
      return null;
    }
  }

  Future<Map<String, dynamic>?> searchStock(String query) async {
    try {
      final response = await _dio.get('/search', queryParameters: {'q': query});
      dynamic data = response.data;
      return data is String ? jsonDecode(data) : data;
    } catch (e) {
      return null;
    }
  }

  // 주식 주문
  Future<Map<String, dynamic>?> placeOrder(String symbol, double quantity, String side) async {
    try {
      print('🚀 [Trade] Ordering $side $quantity shares of $symbol');
      final response = await _dio.post(
        '/trade/order', 
        queryParameters: {
          'symbol': symbol,
          'quantity': quantity,
          'side': side,
        }
      );
      
      dynamic data = response.data;
      if (data is String) data = jsonDecode(data);
      print('✅ [Trade] Success: $data');
      return data;
    } catch (e) {
      if (e is DioException) {
        print('❌ [Trade Error] ${e.response?.statusCode}: ${e.response?.data}');
      }
      return null;
    }
  }
}
