import 'dart:html' as html;

String? getWebStorage(String key) {
  try {
    return html.window.localStorage[key];
  } catch (e) {
    return null;
  }
}

void setWebStorage(String key, String value) {
  try {
    html.window.localStorage[key] = value;
  } catch (e) {}
}

void removeWebStorage(String key) {
  try {
    html.window.localStorage.remove(key);
  } catch (e) {}
}
