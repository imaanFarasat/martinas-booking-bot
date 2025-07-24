#!/usr/bin/env python3
"""
Railway Deployment Helper Script
"""
import os
import subprocess
import sys

def check_git():
    """Check if git is installed and repository is ready"""
    try:
        result = subprocess.run(['git', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Git is installed")
        else:
            print("❌ Git is not installed")
            return False
    except FileNotFoundError:
        print("❌ Git is not installed")
        return False
    
    # Check if this is a git repository
    try:
        result = subprocess.run(['git', 'status'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Git repository found")
            return True
        else:
            print("❌ Not a git repository")
            return False
    except:
        print("❌ Not a git repository")
        return False

def check_files():
    """Check if required files exist"""
    required_files = [
        'main_start.py',
        'bot_async.py',
        'config.py',
        'database_factory.py',
        'database_mysql.py',
        'requirements.txt',
        'railway.toml',
        'Procfile'
    ]
    
    missing_files = []
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file}")
            missing_files.append(file)
    
    return len(missing_files) == 0

def check_env():
    """Check environment variables"""
    print("\n🔍 Checking environment variables...")
    
    bot_token = os.getenv('BOT_TOKEN')
    if bot_token and bot_token != 'YOUR_BOT_TOKEN_HERE':
        print("✅ BOT_TOKEN is set")
    else:
        print("❌ BOT_TOKEN not set")
    
    admin_ids = os.getenv('ADMIN_IDS')
    if admin_ids:
        print("✅ ADMIN_IDS is set")
    else:
        print("❌ ADMIN_IDS not set")

def main():
    """Main deployment check"""
    print("🚀 Railway Deployment Check")
    print("=" * 50)
    
    # Check git
    if not check_git():
        print("\n💡 To fix: Initialize git repository")
        print("   git init")
        print("   git add .")
        print("   git commit -m 'Initial commit'")
        return
    
    # Check files
    print("\n📁 Checking required files...")
    if not check_files():
        print("\n❌ Some required files are missing")
        return
    
    # Check environment
    check_env()
    
    print("\n" + "=" * 50)
    print("✅ Ready for Railway deployment!")
    print("\n📋 Next steps:")
    print("1. Push your code to GitHub:")
    print("   git add .")
    print("   git commit -m 'Prepare for Railway deployment'")
    print("   git push origin main")
    print("\n2. Go to railway.app and create new project")
    print("3. Connect your GitHub repository")
    print("4. Add MySQL database")
    print("5. Set environment variables")
    print("6. Deploy!")

if __name__ == "__main__":
    main() 