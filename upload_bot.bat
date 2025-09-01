@echo off
:: Git identity
git config --global user.name "qwerty-007100"
git config --global user.email "hamidshaymanov2022@gmail.com"

:: TelegramBot papkasi yo‘lini shu yerga yozing
set BOT_DIR=C:\TelegramBot

cd /d "%BOT_DIR%"

:: Remote’ni o‘chirib, yangi remote qo‘shish
git remote remove origin 2>nul

git init
git add .
git commit -m "Add all bot files"
git branch -M main
git remote add origin https://github.com/qwerty-007100/telegram-bot.git

:: Force push bilan hamma fayllarni GitHub’ga tushirish
git push -u origin main --force

pause
