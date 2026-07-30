import 'web_storage_stub.dart' if (dart.library.html) 'web_storage_web.dart';

class WebStorage {
  static String? getItem(String key) => getWebStorage(key);
  static void setItem(String key, String value) => setWebStorage(key, value);
  static void removeItem(String key) => removeWebStorage(key);
}
