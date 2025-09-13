#!/usr/bin/env python3
"""
Capsule AI Commercial Edition - Main Launcher
Integrates AI image generation engine with commercial features
"""

import os
import ssl
import sys
import threading
import time
import subprocess

print('[Capsule AI Commercial Edition] Starting launcher...')
print('[System ARGV] ' + str(sys.argv))

# Setup root path and environment
root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(root)
os.chdir(root)

# Core environment setup
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
os.environ["PYTORCH_MPS_HIGH_WATERMARK_RATIO"] = "0.0"
if "GRADIO_SERVER_PORT" not in os.environ:
    os.environ["GRADIO_SERVER_PORT"] = "7862"  # Commercial port

ssl._create_default_https_context = ssl._create_unverified_context

import platform

def check_commercial_requirements():
    """Check if commercial dependencies are installed"""
    try:
        import flask
        import flask_sqlalchemy
        import bcrypt
        import jwt
        return True
    except ImportError as e:
        print(f"[Commercial Setup] Missing commercial dependencies: {e}")
        print("[Commercial Setup] Installing commercial requirements...")
        return False

def install_commercial_deps():
    """Install commercial dependencies"""
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements-commercial.txt"], check=True)
    print("[Commercial Setup] Commercial dependencies installed successfully!")

def prepare_ai_environment():
    """Prepare AI engine environment"""
    try:
        import capsule_version
        from build_launcher import build_launcher
        from core_modules.launch_util import is_installed, run, python, run_pip, requirements_met
    except ImportError as e:
        print(f"[AI Engine] Import error: {e}")
        return False

    torch_index_url = os.environ.get('TORCH_INDEX_URL', "https://download.pytorch.org/whl/cu121")
    torch_command = os.environ.get('TORCH_COMMAND',
                                   f"pip install torch==2.1.0 torchvision==0.16.0 --extra-index-url {torch_index_url}")
    requirements_file = "requirements_versions.txt"

    print(f"Python {sys.version}")
    print(f"Capsule version: {capsule_version.version}")

    # Install core AI dependencies
    if not is_installed("torch") or not is_installed("torchvision"):
        run(f'"{python}" -m {torch_command}', "Installing torch and torchvision", "Couldn't install torch", live=True)

    if not requirements_met(requirements_file):
        run_pip(f"install -r \"{requirements_file}\"", "AI requirements")

    # Build launcher
    build_launcher()
    print("[AI Engine] Environment prepared successfully!")
    return True

def setup_ai_models():
    """Setup AI models and configurations"""
    try:
        from args_manager import args
        from core_modules import config
        from core_modules.hash_cache import init_cache
        from core_modules.model_loader import load_file_from_url

        # Environment setup
        os.environ["U2NET_HOME"] = config.path_inpaint
        os.environ['GRADIO_TEMP_DIR'] = config.temp_path

        # VAE approx files
        vae_approx_filenames = [
            ('xlvaeapp.pth', 'https://huggingface.co/lllyasviel/misc/resolve/main/xlvaeapp.pth'),
            ('vaeapp_sd15.pth', 'https://huggingface.co/lllyasviel/misc/resolve/main/vaeapp_sd15.pt'),
            ('xl-to-v1_interposer-v4.0.safetensors',
             'https://huggingface.co/mashb1t/misc/resolve/main/xl-to-v1_interposer-v4.0.safetensors')
        ]

        # Download essential models
        for file_name, url in vae_approx_filenames:
            load_file_from_url(url=url, model_dir=config.path_vae_approx, file_name=file_name)

        # Load expansion model
        load_file_from_url(
            url='https://huggingface.co/lllyasviel/misc/resolve/main/fooocus_expansion.bin',
            model_dir=config.path_capsule_expansion,
            file_name='pytorch_model.bin'
        )

        config.update_files()
        init_cache(config.model_filenames, config.paths_checkpoints, config.lora_filenames, config.paths_loras)
        
        print("[AI Models] Model setup completed!")
        return True
    except Exception as e:
        print(f"[AI Models] Error setting up models: {e}")
        return False

def start_commercial_server():
    """Start commercial web server with authentication"""
    print("[Commercial Server] Starting commercial web interface...")
    try:
        # Import and start Flask server with authentication
        from auth.auth_service import create_app
        
        app = create_app()
        app.run(
            host='0.0.0.0',
            port=8080,
            debug=False,
            threaded=True
        )
    except Exception as e:
        print(f"[Commercial Server] Error starting server: {e}")

def start_ai_engine():
    """Start AI image generation engine"""
    print("[AI Engine] Starting AI generation interface...")
    try:
        # Import and start Gradio interface
        import webui
    except Exception as e:
        print(f"[AI Engine] Error starting AI engine: {e}")

def main():
    """Main launcher function"""
    print("🚀 Capsule AI Commercial Edition")
    print("=" * 60)
    print("🎨 Professional AI Image Generation Platform")
    print("💰 With Commercial Features & Payment Integration")
    print("=" * 60)

    # Check and install commercial requirements
    if not check_commercial_requirements():
        try:
            install_commercial_deps()
        except Exception as e:
            print(f"❌ Failed to install commercial dependencies: {e}")
            sys.exit(1)

    # Prepare AI environment
    print("\n[Setup] Preparing AI engine environment...")
    if not prepare_ai_environment():
        print("❌ Failed to prepare AI environment")
        sys.exit(1)

    # Setup AI models
    print("\n[Setup] Setting up AI models...")
    if not setup_ai_models():
        print("❌ Failed to setup AI models")
        sys.exit(1)

    print("\n🎯 Starting Commercial Platform...")
    print("=" * 60)
    print("🌐 Commercial Interface: http://localhost:8080")
    print("🎨 AI Generation Engine: http://localhost:7862")
    print("📊 Authentication & Payment System: Active")
    print("💳 Credits System: Enabled")
    print("=" * 60)

    try:
        # Start commercial server in background thread
        commercial_thread = threading.Thread(target=start_commercial_server, daemon=True)
        commercial_thread.start()

        # Give commercial server time to start
        time.sleep(2)

        # Start AI engine (main thread)
        start_ai_engine()

    except KeyboardInterrupt:
        print("\n👋 Shutting down Capsule AI Commercial Edition...")
    except Exception as e:
        print(f"❌ Error running application: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()