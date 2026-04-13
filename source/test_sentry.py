# test_sentry.py
"""
Quick test to verify Sentry is capturing errors.
Run this ONCE to test, then check Sentry dashboard.
"""

from dotenv import load_dotenv
import os

load_dotenv()

import sentry_sdk

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    send_default_pii=True,
    traces_sample_rate=1.0,  # Capture 100% for testing
)

print("🧪 Testing Sentry error capture...\n")

# Test 1: Captured exception (con try-except)
print("1️⃣ Sending a captured error to Sentry...")
try:
    result = 1 / 0  # ZeroDivisionError
except ZeroDivisionError as e:
    print(f"   ✅ Error caught: {e}")
    sentry_sdk.capture_exception(e)  # Invia manualmente a Sentry
    print("   📤 Sent to Sentry!")

# Wait for Sentry to flush
import time
time.sleep(2)

# Test 2: Unhandled exception (crasha il programma)
print("\n2️⃣ Triggering an UNHANDLED error (script will crash)...")
print("   This simulates a real production bug.")
time.sleep(1)

# Questo NON ha try-except, Sentry lo cattura automaticamente
missing_list = []
print(missing_list[999])  # 💥 IndexError - Sentry cattura automaticamente!