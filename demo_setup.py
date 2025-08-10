import streamlit as st
import subprocess
import sys

def check_installation():
    """Check if all required packages are installed"""
    required_packages = [
        'streamlit', 'torch', 'transformers', 'newspaper3k',
        'beautifulsoup4', 'requests', 'validators', 'plotly'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("Run: pip install " + " ".join(missing_packages))
        return False
    else:
        print("✅ All packages installed correctly!")
        return True

def run_demo():
    """Run the complete demo setup"""
    print("🎯 AICTE Lab Demo Setup")
    print("=" * 50)
    
    if check_installation():
        print("🚀 Starting Streamlit app...")
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])
    else:
        print("❌ Please install missing packages first")

if __name__ == "__main__":
    run_demo()
    