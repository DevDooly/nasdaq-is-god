import 'url_launcher_stub.dart'
    if (dart.library.html) 'url_launcher_web.dart';

void launchInNewTab(String url) {
  openUrlInNewTab(url);
}
