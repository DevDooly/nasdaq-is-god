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
    connectTimeout: const Duration(seconds: 10),
    receiveTimeout: const Duration(seconds: 10),
  ));

  final _storage = const FlutterSecureStorage();

  ApiService() {
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        String? token = await _storage.read(key: 'jwt_token');
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        return handler.next(options);
      },
    ));
  }

  // 로그인
  Future<Map<String, dynamic>?> login(String username, String password) async {
    try {
      print('🔑 [Login Attempt] User: $username at $_baseUrl');
      
      final response = await _dio.post(
        '/login',
        data: {
          'username': username,
          'password': password,
        },
        options: Options(
          contentType: Headers.formUrlEncodedContentType,
          responseType: ResponseType.json,
        ),
      );
      
      print('✅ [Login Response] Status: ${response.statusCode}');
      
      dynamic data = response.data;
      if (data is String) {
        data = jsonDecode(data);
      }

      if (response.statusCode == 200 && data != null) {
        final token = data['access_token'];
        if (token != null) {
          try {
            await _storage.write(key: 'jwt_token', value: token);
            print('💾 [Login Storage] Token saved');
          } catch (e) {
            print('⚠️ [Login Storage Warning] $e');
          }
          return data;
        }
      }
      return null;
    } catch (e) {
      print('🚨 [Login API Error] $e');
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
}