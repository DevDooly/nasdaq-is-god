import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter/foundation.dart';
import 'dart:convert';
import 'dart:html' as html;

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

  final _storage = const FlutterSecureStorage();

  ApiService() {
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        String? token;
        
        // 💡 웹 환경에서는 LocalStorage에서 직접 읽는 것이 더 안정적일 수 있음
        if (kIsWeb) {
          token = html.window.localStorage['jwt_token'];
        } else {
          token = await _storage.read(key: 'jwt_token');
        }

        if (token != null && token.isNotEmpty) {
          options.headers['Authorization'] = 'Bearer $token';
          print('🔑 [Auth] Token 부착됨: ${options.path}');
        } else {
          print('⚠️ [Auth] 전송할 Token이 없음: ${options.path}');
        }
        return handler.next(options);
      },
      onError: (DioException e, handler) {
        print('❌ [API Error] ${e.response?.statusCode} - ${e.message}');
        return handler.next(e);
      },
    ));
  }

  // 로그인
  Future<Map<String, dynamic>?> login(String username, String password) async {
    try {
      print('🔑 [Login] Attempting for $username');
      
      final formData = FormData.fromMap({
        'username': username,
        'password': password,
      });

      final response = await _dio.post(
        '/login',
        data: formData,
        options: Options(
          contentType: Headers.formUrlEncodedContentType,
        ),
      );
      
      dynamic data = response.data;
      if (data is String) data = jsonDecode(data);

      if (response.statusCode == 200 && data != null) {
        final token = data['access_token'];
        if (token != null) {
          // 💡 웹과 앱 모두에서 토큰 저장
          if (kIsWeb) {
            html.window.localStorage['jwt_token'] = token;
          }
          await _storage.write(key: 'jwt_token', value: token);
          print('✅ [Login] 성공 및 토큰 저장 완료');
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
      print('🚀 [Trade] 주문 전송: $side $symbol $quantity');
      // 💡 queryParameters 대신 data(Body)로 전송 시도 (CORS 이슈 대응)
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
      print('✅ [Trade] 주문 결과: $data');
      return data;
    } catch (e) {
      if (e is DioException) {
        print('❌ [Trade Error] ${e.response?.statusCode}: ${e.response?.data}');
      }
      return null;
    }
  }
}