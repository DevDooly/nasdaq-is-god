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

  Future<Options> _getAuthOptions() async {
    String? token;
    if (kIsWeb) {
      token = html.window.localStorage['jwt_token'];
    } else {
      token = await _storage.read(key: 'jwt_token');
    }
    return Options(
      headers: {
        if (token != null) 'Authorization': 'Bearer $token',
      },
    );
  }

  // 로그인
  Future<Map<String, dynamic>?> login(String username, String password) async {
    try {
      print('🔑 [Login Attempt] URL: $_baseUrl/login');
      
      // FastAPI OAuth2 표준: x-www-form-urlencoded
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
      
      print('✅ [Login Server Response] Status: ${response.statusCode}');
      print('📦 [Login Body] ${response.data}');
      
      dynamic data = response.data;
      if (data is String) data = jsonDecode(data);

      if (data != null && data['access_token'] != null) {
        final token = data['access_token'];
        if (kIsWeb) {
          html.window.localStorage['jwt_token'] = token;
        }
        await _storage.write(key: 'jwt_token', value: token);
        print('💾 [Login] Token saved successfully');
        return data;
      }
      
      print('❌ [Login] Token not found in response body');
      return null;
    } catch (e) {
      if (e is DioException) {
        print('🚨 [Login Dio Error] Status: ${e.response?.statusCode}');
        print('🚨 [Login Dio Error Body] ${e.response?.data}');
      } else {
        print('🚨 [Login Unknown Error] $e');
      }
      return null;
    }
  }

  Future<Map<String, dynamic>?> getMe() async {
    try {
      final options = await _getAuthOptions();
      final response = await _dio.get('/users/me', options: options);
      return response.data is String ? jsonDecode(response.data) : response.data;
    } catch (e) {
      return null;
    }
  }

  Future<List<dynamic>?> getPortfolio() async {
    try {
      final options = await _getAuthOptions();
      final response = await _dio.get('/portfolio', options: options);
      return response.data is String ? jsonDecode(response.data) : response.data;
    } catch (e) {
      return null;
    }
  }

  Future<Map<String, dynamic>?> getIndicators(String symbol) async {
    try {
      final response = await _dio.get('/stock/$symbol/indicators');
      return response.data is String ? jsonDecode(response.data) : response.data;
    } catch (e) {
      return null;
    }
  }

  Future<Map<String, dynamic>?> searchStock(String query) async {
    try {
      final response = await _dio.get('/search', queryParameters: {'q': query});
      return response.data is String ? jsonDecode(response.data) : response.data;
    } catch (e) {
      return null;
    }
  }

  // 주식 주문
  Future<Map<String, dynamic>?> placeOrder(String symbol, double quantity, String side) async {
    try {
      final options = await _getAuthOptions();
      final response = await _dio.post(
        '/trade/order', 
        queryParameters: {
          'symbol': symbol,
          'quantity': quantity,
          'side': side,
        },
        options: options,
      );
      
      dynamic data = response.data;
      if (data is String) data = jsonDecode(data);
      return data;
    } catch (e) {
      return null;
    }
  }
}
