import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class ApiService {
  final Dio _dio = Dio(BaseOptions(
    baseUrl: 'http://localhost:8001', // Changed to 8001 to avoid conflict
    connectTimeout: const Duration(seconds: 5),
    receiveTimeout: const Duration(seconds: 3),
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
      final response = await _dio.post('/login', data: {
        'username': username,
        'password': password,
      }, options: Options(contentType: Headers.formUrlEncodedContentType));
      
      String token = response.data['access_token'];
      await _storage.write(key: 'jwt_token', value: token);
      return response.data;
    } catch (e) {
      print('Login Error: $e');
      return null;
    }
  }

  // 내 정보 조회
  Future<Map<String, dynamic>?> getMe() async {
    try {
      final response = await _dio.get('/users/me');
      return response.data;
    } catch (e) {
      return null;
    }
  }

  // 포트폴리오 조회
  Future<List<dynamic>?> getPortfolio() async {
    try {
      final response = await _dio.get('/portfolio');
      return response.data;
    } catch (e) {
      return null;
    }
  }

  // 주식 주문
  Future<Map<String, dynamic>?> placeOrder(String symbol, double quantity, String side) async {
    try {
      final response = await _dio.post('/trade/order', queryParameters: {
        'symbol': symbol,
        'quantity': quantity,
        'side': side,
      });
      return response.data;
    } catch (e) {
      return null;
    }
  }

  // 지표 데이터 조회
  Future<Map<String, dynamic>?> getIndicators(String symbol) async {
    try {
      final response = await _dio.get('/stock/$symbol/indicators');
      return response.data;
    } catch (e) {
      print('Fetch Indicators Error: $e');
      return null;
    }
  }
}
