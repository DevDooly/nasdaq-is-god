import 'dart:html' as html;

void openUrlInNewTab(String url) {
  if (url.isEmpty) return;
  String targetUrl = url.trim();
  if (!targetUrl.startsWith('http://') && !targetUrl.startsWith('https://')) {
    targetUrl = 'https://$targetUrl';
  }
  try {
    html.window.open(targetUrl, '_blank');
  } catch (e) {
    // fallback
  }
}
