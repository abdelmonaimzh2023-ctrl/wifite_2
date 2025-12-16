#!/bin/bash

# ==========================================================
# Wifite Pro GUI - Setup and Run Script (Combined)
# ==========================================================

# 1. الانتقال إلى مسار السكريبت (ضروري لعمل المسارات النسبية)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# تعيين الأسماء المتغيرة
RUN_SCRIPT_NAME="run_wifite.sh"
APP_FILE="wifite_pro_gui.py"
DESKTOP_FILE="wifite-pro.desktop"
ICON_NAME="wifite_pro_icon.png"
APP_NAME="Wifite Pro GUI"

# 2. خطوة الإعداد (تنفذ مرة واحدة إذا لم يتم تثبيت ملف الإطلاق)
if [ ! -f ~/.local/share/applications/"$DESKTOP_FILE" ]; then
    echo "--- Running First-Time Setup ---"
    
    # أ. إنشاء ملف أيقونة وهمي إذا لم يكن موجوداً
    if [ ! -f "$ICON_NAME" ]; then
        echo "Creating placeholder icon file: $ICON_NAME"
        touch "$ICON_NAME" 
    fi

    # ب. إنشاء ملف .desktop
    echo "Creating desktop entry file: $DESKTOP_FILE"
    DESKTOP_ENTRY_CONTENT="[Desktop Entry]
Version=1.0
Type=Application
Name=$APP_NAME
Comment=Full GUI for Wifite2/Aircrack-ng suite
Exec=$SCRIPT_DIR/$RUN_SCRIPT_NAME
Icon=$SCRIPT_DIR/$ICON_NAME
Terminal=true
Categories=Network;Security;
"
    echo "$DESKTOP_ENTRY_CONTENT" > "$DESKTOP_FILE"

    # ج. تثبيت ملف الإطلاق
    echo "Installing desktop shortcut and application menu entry..."
    mkdir -p ~/.local/share/applications
    cp "$DESKTOP_FILE" ~/.local/share/applications/

    cp "$DESKTOP_FILE" ~/Desktop/

    # منح صلاحيات التنفيذ
    chmod +x ~/.local/share/applications/"$DESKTOP_FILE"
    chmod +x ~/Desktop/"$DESKTOP_FILE"
    
    echo "--- Setup Complete ---"
fi

# 3. تشغيل الأداة (يتم تنفيذه دائماً)
echo "Running $APP_NAME now..."
sudo python3 "$APP_FILE"
