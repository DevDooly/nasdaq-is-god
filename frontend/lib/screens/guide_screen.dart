import 'package:flutter/material.dart';

class GuideScreen extends StatelessWidget {
  const GuideScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF020617), // Slate 950
      appBar: AppBar(
        title: const Text('📖 주식 매매기법 & AI 하이브리드 가이드북'),
        backgroundColor: const Color(0xFF0F172A),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 1. 헤더 배너
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [Color(0xFF06B6D4), Color(0xFF3B82F6)],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(20),
                boxShadow: [
                  BoxShadow(
                    color: const Color(0xFF06B6D4).withValues(alpha: 0.3),
                    blurRadius: 15,
                    offset: const Offset(0, 8),
                  )
                ],
              ),
              child: const Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Nasdaq is God 📈', style: TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.bold)),
                  SizedBox(height: 8),
                  Text(
                    '퀀트 기술적 매매기법 백테스팅과 AI 기반 뉴스/트위터 감성 분석을 결합한 하이브리드 자동매매 시스템 활용 가이드입니다.',
                    style: TextStyle(color: Colors.white70, fontSize: 14, height: 1.5),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),

            // 2. 백테스팅 성과 지표 가이드
            const Text('📊 백테스팅 성과 지표 보는 법', style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 12),
            _buildGuideCard(
              icon: Icons.analytics,
              iconColor: const Color(0xFF06B6D4),
              title: '핵심 지표 해석 공식',
              items: [
                {'title': 'Total Return (누적 수익률)', 'desc': '초기 자금 대비 시뮬레이션 기간 동안의 총 자산 증가 비율(%)입니다.'},
                {'title': 'CAGR (연평균 성장률)', 'desc': '복리 효과를 감안한 연간 평균 수익률입니다.'},
                {'title': 'Max Drawdown (MDD, 최대 낙폭)', 'desc': '고점 대비 경험할 수 있는 최대 손실 폭(%)으로, 리스크 관리의 핵심 지표입니다.'},
                {'title': 'Sharpe Ratio (위험 대비 수익비)', 'desc': '변동성(위험) 1단위당 얻은 초과 수익률로, 1.0 이상이면 우수한 전략입니다.'},
                {'title': 'Profit Factor (손익비)', 'desc': '총 이익 ÷ 총 손실 비율로, 1.5 이상일 때 장기 우상향 가능성이 높습니다.'},
              ],
            ),
            const SizedBox(height: 24),

            // 3. 5대 전통 기술적 매매기법
            const Text('📈 5대 기술적 매매기법 설명서', style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 12),
            _buildStrategyCard(
              tag: 'MA Crossover',
              title: '1. 이동평균선 골든/데드 크로스',
              desc: '단기 이동평균선(20일)이 장기 이동평균선(50일)을 위로 뚫을 때 상승 추세 시작으로 판단하여 매수하고, 하향 돌파 시 매도합니다.',
              color: Colors.blueAccent,
            ),
            _buildStrategyCard(
              tag: 'RSI Reversal',
              title: '2. RSI 과매도/과매수 반등 전략',
              desc: 'RSI 지표가 30 이하(과매도)에서 반등 탈출할 때 눌림목 매수하고, 70 이상(과매수)에서 꺾일 때 차익 실현 매도합니다.',
              color: Colors.purpleAccent,
            ),
            _buildStrategyCard(
              tag: 'MACD Trend',
              title: '3. MACD 히스토그램 크로스',
              desc: 'MACD선이 시그널선을 상향 돌파(골든크로스)하며 히스토그램이 양수로 전환될 때 강한 추세 전환으로 판단하여 매수합니다.',
              color: Colors.amberAccent,
            ),
            _buildStrategyCard(
              tag: 'Bollinger Bands',
              title: '4. 볼린저 밴드 이탈 반등',
              desc: '주가가 볼린저 밴드 하단에 터치 후 반등할 때 기술적 반등을 노려 매수하고, 상단 밴드 도달 시 매도합니다.',
              color: Colors.cyanAccent,
            ),
            _buildStrategyCard(
              tag: 'Dual Momentum',
              title: '5. 듀얼 모멘텀 (추세 추종)',
              desc: '특정 룩백 기간 동안 정(Positive)의 모멘텀을 유지하며 시장 평균보다 상승세가 강한 주식을 선택하여 매매합니다.',
              color: Colors.greenAccent,
            ),
            const SizedBox(height: 24),

            // 4. 하이브리드 AI 결합 가이드
            const Text('🤖 기술 지표 + AI 센티먼트 하이브리드 결합', style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(18),
              decoration: BoxDecoration(
                color: const Color(0xFF0F172A),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: const Color(0xFF10B981).withValues(alpha: 0.5)),
              ),
              child: const Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('💡 하이브리드 스코어 산출 공식', style: TextStyle(color: Color(0xFF10B981), fontSize: 16, fontWeight: FontWeight.bold)),
                  SizedBox(height: 10),
                  SelectableText(
                    'Hybrid Score = (Technical Score × W_tech) + (Sentiment Score × (1 - W_tech))',
                    style: TextStyle(color: Colors.white, fontFamily: 'monospace', fontWeight: FontWeight.bold),
                  ),
                  SizedBox(height: 12),
                  Text('• Technical Score (0~100): 기술적 지표의 매수 우위도를 수치화', style: TextStyle(color: Colors.white70, fontSize: 13)),
                  Text('• Sentiment Score (0~100): Gemini AI가 수집한 뉴스 + StockTwits + 월가 대가(Elon Musk, Cathie Wood 등)의 트윗 감성 수치', style: TextStyle(color: Colors.white70, fontSize: 13)),
                  Text('• 자동 주문 발동: 하이브리드 총점이 70점 이상이면 자동 매수, 35점 이하이면 자동 매도 집행', style: TextStyle(color: Colors.white70, fontSize: 13)),
                ],
              ),
            ),
            const SizedBox(height: 30),
          ],
        ),
      ),
    );
  }

  Widget _buildGuideCard({required IconData icon, required Color iconColor, required String title, required List<Map<String, String>> items}) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: const Color(0xFF0F172A),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white10),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, color: iconColor, size: 22),
              const SizedBox(width: 10),
              Text(title, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16)),
            ],
          ),
          const Divider(color: Colors.white10, height: 24),
          ...items.map((item) => Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('• ', style: TextStyle(color: Color(0xFF06B6D4), fontWeight: FontWeight.bold)),
                Expanded(
                  child: RichText(
                    text: TextSpan(
                      children: [
                        TextSpan(text: '${item['title']}: ', style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 13)),
                        TextSpan(text: item['desc'], style: const TextStyle(color: Colors.white70, fontSize: 13)),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          )),
        ],
      ),
    );
  }

  Widget _buildStrategyCard({required String tag, required String title, required String desc, required Color color}) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF0F172A),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: color.withValues(alpha: 0.3)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
            decoration: BoxDecoration(
              color: color.withValues(alpha: 0.15),
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: color),
            ),
            child: Text(tag, style: TextStyle(color: color, fontWeight: FontWeight.bold, fontSize: 12)),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 15)),
                const SizedBox(height: 6),
                Text(desc, style: const TextStyle(color: Colors.white70, fontSize: 13, height: 1.4)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
