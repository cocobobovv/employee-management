# APK 构建指南

## 方式一：PWA 安装（最简单，无需构建）

在手机浏览器中访问部署后的网址，然后：

- **Android (Chrome)**：点菜单 → "添加到主屏幕"
- **iPhone (Safari)**：点分享按钮 → "添加到主屏幕"

效果和原生 APK 几乎一样，支持全屏、离线缓存。

## 方式二：构建 APK

### 前置要求

1. **Node.js** ≥ 18 （[下载](https://nodejs.org)）
2. **Android Studio** + Android SDK （[下载](https://developer.android.com/studio)）
3. **JAVA JDK** 17+

### Windows 构建

```bash
cd cordova
build-apk.bat
```

### macOS / Linux 构建

```bash
cd cordova
# 安装 Cordova
npm install -g cordova

# 创建项目
cordova create . com.employee.management "员工管理系统"

# 复制配置和页面
cp config.xml www/../
cp -r www/* www/

# 添加 Android 平台
cordova platform add android

# 构建 APK
cordova build android --release
```

### 构建产物

APK 文件位置：
```
cordova/platforms/android/app/build/outputs/apk/release/
```

### 自定义服务器地址

如果要修改 APK 加载的服务器地址，编辑：
```
cordova/www/index.html  → 修改 iframe 的 src 属性
```

例如改成你自己的域名：
```html
<iframe src="https://你的域名.com/login"></iframe>
```
