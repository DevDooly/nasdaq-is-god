import 'package:flutter/material.dart';
import 'services/api_service.dart';
import 'screens/home_screen.dart';
import 'screens/login_screen.dart';

void main() {
  runApp(const NasdaqGodApp());
}

class NasdaqGodApp extends StatefulWidget {
  const NasdaqGodApp({super.key});

  @override
  State<NasdaqGodApp> createState() => _NasdaqGodAppState();
}

class _NasdaqGodAppState extends State<NasdaqGodApp> {
  final ApiService _apiService = ApiService();
  bool _isCheckingAuth = true;
  bool _isAuthenticated = false;

  @override
  void initState() {
    super.initState();
    _checkAuth();
  }

  Future<void> _checkAuth() async {
    final token = await _apiService.getValidToken();
    if (token != null) {
      final user = await _apiService.getMe();
      if (user != null) {
        setState(() {
          _isAuthenticated = true;
        });
      } else {
        await _apiService.logout();
      }
    }
    setState(() {
      _isCheckingAuth = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_isCheckingAuth) {
      return MaterialApp(
        debugShowCheckedModeBanner: false,
        theme: ThemeData(brightness: Brightness.dark),
        home: const Scaffold(body: Center(child: CircularProgressIndicator())),
      );
    }

    return MaterialApp(
      title: 'Nasdaq is God',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.dark,
        primarySwatch: Colors.blue,
        useMaterial3: true,
        scaffoldBackgroundColor: const Color(0xFF0F172A),
        appBarTheme: const AppBarTheme(
          backgroundColor: Color(0xFF0F172A),
          elevation: 0,
        ),
      ),
      home: _isAuthenticated ? const HomeScreen() : const LoginScreen(),
    );
  }
}
