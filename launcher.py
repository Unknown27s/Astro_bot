#!/usr/bin/env python
"""
AstroBot Diagnostics & Server Launcher
Validates environment and starts servers with proper error handling
"""

import os
import sys
import subprocess
import socket
import time
from pathlib import Path

class AstroBotDiagnostics:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.errors = []
        self.warnings = []
        
    def check_python_version(self):
        """Verify Python 3.9+"""
        print("[*] Checking Python version...")
        if sys.version_info < (3, 9):
            self.errors.append(f"Python 3.9+ required, got {sys.version}")
            return False
        print(f"    [OK] Python {sys.version.split()[0]}")
        return True
    
    def check_port_available(self, port):
        """Check if a port is available"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            return result != 0
        except:
            return True
    
    def check_ports(self):
        """Check if required ports are available"""
        print("[*] Checking ports...")
        ports = {8000: "FastAPI", 8080: "Spring Boot", 3000: "React"}
        all_available = True
        
        for port, service in ports.items():
            if self.check_port_available(port):
                print(f"    [OK] Port {port:5d} ({service}) - Available")
            else:
                msg = f"Port {port} ({service}) - IN USE"
                print(f"    [ERROR] {msg}")
                self.warnings.append(msg)
                all_available = False
        
        return all_available
    
    def check_dependencies(self):
        """Check Python package dependencies"""
        print("[*] Checking Python dependencies...")
        required = [
            "fastapi", "uvicorn", "pydantic", "chromadb",
            "sentence_transformers", "requests", "python_dotenv",
            "PyPDF2", "python_docx", "openpyxl"
        ]
        
        missing = []
        for pkg in required:
            try:
                __import__(pkg.replace("-", "_"))
                print(f"    [OK] {pkg}")
            except ImportError:
                print(f"    [ERROR] {pkg} - NOT INSTALLED")
                missing.append(pkg)
        
        if missing:
            self.errors.append(f"Missing packages: {', '.join(missing)}")
            return False
        return True
    
    def check_env_file(self):
        """Check .env configuration"""
        print("[*] Checking .env file...")
        env_path = self.project_root / ".env"
        
        if not env_path.exists():
            self.warnings.append(".env file not found - using defaults")
            return True
        
        # Read .env and check for key variables
        required_vars = [
            "LLM_MODE", "OLLAMA_BASE_URL", "EMBEDDING_MODEL",
            "CHUNK_SIZE", "CHUNK_OVERLAP", "SQLITE_DB_PATH"
        ]
        
        env_content = env_path.read_text()
        found_vars = []
        
        for var in required_vars:
            if var in env_content:
                found_vars.append(var)
                print(f"    [OK] {var} configured")
            else:
                print(f"    [WARN] {var} not found")
        
        if len(found_vars) < len(required_vars) / 2:
            self.warnings.append("Several .env variables missing")
        
        return True
    
    def check_database(self):
        """Check database connectivity"""
        print("[*] Checking database...")
        try:
            from database.db import init_db, get_connection
            init_db()
            conn = get_connection()
            user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            conn.close()
            print(f"    [OK] SQLite database ready ({user_count} users)")
            return True
        except Exception as e:
            self.errors.append(f"Database error: {e}")
            return False
    
    def check_chromadb(self):
        """Check ChromaDB availability"""
        print("[*] Checking ChromaDB...")
        try:
            from ingestion.embedder import get_collection
            col = get_collection()
            print(f"    [OK] ChromaDB ready ({col.count()} vectors)")
            return True
        except Exception as e:
            self.warnings.append(f"ChromaDB warning: {e}")
            return True  # Not critical
    
    def check_llm_provider(self):
        """Check LLM provider availability"""
        print("[*] Checking LLM providers...")
        try:
            from rag.providers.manager import get_manager
            manager = get_manager()
            statuses = manager.get_all_statuses()
            
            for provider, status in statuses.items():
                if status == "ok":
                    print(f"    [OK] {provider.upper()}")
                else:
                    print(f"    [WARN] {provider.upper()} - {status}")
            
            return True
        except Exception as e:
            self.warnings.append(f"LLM provider error: {e}")
            return True
    
    def run_diagnostics(self):
        """Run all diagnostic checks"""
        print("\n" + "="*60)
        print("IMS AstroBot Diagnostics")
        print("="*60 + "\n")
        
        checks = [
            self.check_python_version,
            self.check_ports,
            self.check_dependencies,
            self.check_env_file,
            self.check_database,
            self.check_chromadb,
            self.check_llm_provider,
        ]
        
        for check in checks:
            try:
                check()
            except Exception as e:
                self.errors.append(f"Diagnostic error in {check.__name__}: {e}")
            print()
        
        return self.print_summary()
    
    def print_summary(self):
        """Print diagnostic summary"""
        print("="*60)
        
        if not self.errors and not self.warnings:
            print("STATUS: All checks passed!")
            print("="*60)
            return True
        
        if self.errors:
            print("ERRORS (system may not work properly):")
            for err in self.errors:
                print(f"  [!] {err}")
        
        if self.warnings:
            print("\nWARNINGS (may cause issues):")
            for warn in self.warnings:
                print(f"  [*] {warn}")
        
        print("="*60)
        return len(self.errors) == 0
    
    def start_servers(self):
        """Start servers based on user choice"""
        print("\nWhich servers would you like to start?")
        print("  1. FastAPI only (8000)")
        print("  2. React only (3000)")
        print("  3. Spring Boot only (8080)")
        print("  4. All three (recommended)")
        print("  5. Diagnostics only (no servers)")
        print("  6. Exit")
        
        try:
            choice = input("\nEnter choice (1-6): ").strip()
        except KeyboardInterrupt:
            print("\nExiting...")
            return
        
        servers = {
            "1": self.start_fastapi,
            "2": self.start_react,
            "3": self.start_spring,
            "4": self.start_all,
        }
        
        if choice in servers:
            servers[choice]()
        elif choice == "5":
            print("Diagnostics complete.")
        elif choice == "6":
            print("Exiting...")
        else:
            print("Invalid choice.")
    
    def start_fastapi(self):
        """Start FastAPI server"""
        print("\n[+] Starting FastAPI server on http://localhost:8000")
        print("    API docs: http://localhost:8000/docs")
        print("    (Press Ctrl+C to stop)\n")
        
        os.chdir(self.project_root)
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "api_server:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ])
    
    def start_react(self):
        """Start React frontend"""
        react_dir = self.project_root / "react-frontend"
        print("\n[+] Starting React frontend on http://localhost:3000")
        print("    (Press Ctrl+C to stop)\n")
        
        os.chdir(react_dir)
        subprocess.run(["npm", "run", "dev"])
    
    def start_spring(self):
        """Start Spring Boot"""
        spring_dir = self.project_root / "springboot-backend"
        print("\n[+] Starting Spring Boot on http://localhost:8080")
        print("    (Press Ctrl+C to stop)\n")
        
        os.chdir(spring_dir)
        if os.name == 'nt':
            subprocess.run(["mvnw.cmd", "spring-boot:run"])
        else:
            subprocess.run(["./mvnw", "spring-boot:run"])
    
    def start_all(self):
        """Start all three servers"""
        print("\n[+] Starting all servers...")
        print("    FastAPI:    http://localhost:8000")
        print("    React:      http://localhost:3000")
        print("    Spring:     http://localhost:8080")
        print()
        
        import threading
        
        threads = [
            threading.Thread(target=self.start_fastapi, daemon=True),
            threading.Thread(target=self.start_react, daemon=True),
            threading.Thread(target=self.start_spring, daemon=True),
        ]
        
        for t in threads:
            t.start()
            time.sleep(2)
        
        print("\nAll servers started. Press Ctrl+C to stop all.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down...")

def main():
    diag = AstroBotDiagnostics()
    
    # Run diagnostics
    all_ok = diag.run_diagnostics()
    
    # Optionally start servers
    if all_ok or input("\nProceed anyway? (y/n): ").lower() == 'y':
        diag.start_servers()

if __name__ == "__main__":
    main()
