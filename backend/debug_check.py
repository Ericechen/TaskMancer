import asyncio
import sys
import os

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from config_parser import ConfigParser
    print("ConfigParser imported successfully.")
except Exception as e:
    print(f"Failed to import ConfigParser: {e}")
    sys.exit(1)

try:
    from live_utils import PortScanner
    print("PortScanner imported successfully.")
except Exception as e:
    print(f"Failed to import PortScanner: {e}")
    sys.exit(1)

async def test_scanner():
    print("Testing PortScanner...")
    try:
        # Test 1: Scan localhost:8000 (assuming it might be running or not)
        # using localhost for host
        result = await PortScanner.get_port_status("localhost", 8000, "Backend")
        print(f"Scan result: {result}")
        
        # Test 2: Scan with explicitly None
        # PortScanner.scan_ports expects explict_ports list or None
        results = await PortScanner.scan_ports(explicit_ports=[])
        print(f"Explicit empty scan results: {results}")

    except Exception as e:
        print(f"Scanner test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_scanner())
