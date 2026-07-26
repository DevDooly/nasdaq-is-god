import 'package:flutter/material.dart';
import '../services/api_service.dart';
import 'home_screen.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _usernameController = TextEditingController();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _apiService = ApiService();
  bool _isSignUpMode = false;
  bool _isLoading = false;

  void _handleSubmit() async {
    if (_usernameController.text.isEmpty || _passwordController.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('아이디와 비밀번호를 입력해주세요.')));
      return;
    }

    setState(() => _isLoading = true);

    if (_isSignUpMode) {
      final email = _emailController.text.isEmpty ? '${_usernameController.text}@example.com' : _emailController.text;
      final success = await _apiService.signup(_usernameController.text, email, _passwordController.text);
      if (mounted) {
        if (success) {
          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('회원가입 성공! 로그인합니다.')));
          // 가입 성공 후 즉시 로그인 처리
          _handleLogin();
        } else {
          setState(() => _isLoading = false);
          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('회원가입 실패: 이미 존재하는 아이디일 수 있습니다.')));
        }
      }
    } else {
      _handleLogin();
    }
  }

  void _handleLogin() async {
    final result = await _apiService.login(_usernameController.text, _passwordController.text);
    if (mounted) {
      setState(() => _isLoading = false);
      if (result != null) {
        Navigator.of(context).pushReplacement(MaterialPageRoute(builder: (context) => const HomeScreen()));
      } else {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('인증 실패: 아이디 또는 비밀번호를 확인하세요.')));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF020617),
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 24),
          child: Container(
            constraints: const BoxConstraints(maxWidth: 400),
            padding: const EdgeInsets.all(40),
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.02),
              borderRadius: BorderRadius.circular(24),
              border: Border.all(color: Colors.white.withOpacity(0.05)),
              boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.5), blurRadius: 40)],
            ),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(Icons.auto_graph, color: Colors.cyanAccent, size: 64),
                const SizedBox(height: 24),
                const Text('나스닥의 신', style: TextStyle(fontSize: 24, fontWeight: FontWeight.w900, letterSpacing: 4)),
                const Text('퀀트 터미널 v2.0', style: TextStyle(fontSize: 10, color: Colors.grey, letterSpacing: 2)),
                const SizedBox(height: 32),
                
                // 로그인 / 회원가입 전환 탭
                Row(
                  children: [
                    Expanded(
                      child: GestureDetector(
                        onTap: () => setState(() => _isSignUpMode = false),
                        child: Container(
                          padding: const EdgeInsets.symmetric(vertical: 12),
                          decoration: BoxDecoration(
                            border: Border(bottom: BorderSide(color: !_isSignUpMode ? Colors.cyanAccent : Colors.transparent, width: 2)),
                          ),
                          child: Center(
                            child: Text('로그인', style: TextStyle(color: !_isSignUpMode ? Colors.cyanAccent : Colors.grey, fontWeight: FontWeight.bold)),
                          ),
                        ),
                      ),
                    ),
                    Expanded(
                      child: GestureDetector(
                        onTap: () => setState(() => _isSignUpMode = true),
                        child: Container(
                          padding: const EdgeInsets.symmetric(vertical: 12),
                          decoration: BoxDecoration(
                            border: Border(bottom: BorderSide(color: _isSignUpMode ? Colors.cyanAccent : Colors.transparent, width: 2)),
                          ),
                          child: Center(
                            child: Text('회원가입', style: TextStyle(color: _isSignUpMode ? Colors.cyanAccent : Colors.grey, fontWeight: FontWeight.bold)),
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 32),

                _buildField(
                  '아이디',
                  _usernameController,
                  false,
                  action: TextInputAction.next,
                ),
                if (_isSignUpMode) ...[
                  const SizedBox(height: 16),
                  _buildField(
                    '이메일 (선택)',
                    _emailController,
                    false,
                    action: TextInputAction.next,
                  ),
                ],
                const SizedBox(height: 16),
                _buildField(
                  '비밀번호',
                  _passwordController,
                  true,
                  action: TextInputAction.done,
                  onSubmitted: (_) => _handleSubmit(),
                ),
                const SizedBox(height: 32),
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: _isLoading ? null : _handleSubmit,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.cyanAccent[700],
                      padding: const EdgeInsets.all(20),
                    ),
                    child: _isLoading 
                      ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                      : Text(_isSignUpMode ? '회원가입하기' : '로그인', style: const TextStyle(fontWeight: FontWeight.bold, letterSpacing: 1.5)),
                  ),
                ),
                const SizedBox(height: 16),
                Text(
                  _isSignUpMode ? '이미 계정이 있으신가요? 상단 로그인 탭을 선택하세요.' : '💡 기본 관리자 계정: admin / admin1234',
                  style: const TextStyle(fontSize: 11, color: Colors.grey),
                  textAlign: TextAlign.center,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildField(String label, TextEditingController ctrl, bool secret, {TextInputAction? action, Function(String)? onSubmitted}) {
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text(label, style: const TextStyle(fontSize: 10, color: Colors.grey, fontWeight: FontWeight.bold, letterSpacing: 1)),
      const SizedBox(height: 8),
      TextField(
        controller: ctrl,
        obscureText: secret,
        textInputAction: action,
        onSubmitted: onSubmitted,
        style: const TextStyle(fontFamily: 'monospace', color: Colors.white),
        decoration: InputDecoration(
          filled: true,
          fillColor: Colors.white.withOpacity(0.03),
          border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
          contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
        ),
      ),
    ]);
  }
}