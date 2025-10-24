
from kiteconnect import KiteConnect

class ZerodhaClient:
    def __init__(self, api_key=None, api_secret=None, access_token=None):
        self.kite = None
        self.connected = False
        if api_key and api_secret and access_token:
            try:
                self.kite = KiteConnect(api_key=api_key)
                self.kite.set_access_token(access_token)
                self.connected = True
            except Exception as e:
                print(f"Failed to connect to Zerodha: {e}")
        else:
            print("Zerodha credentials not provided. Skipping connection.")

    def get_holdings(self):
        if self.connected:
            return self.kite.holdings()
        return {"error": "Not connected"}

    def get_positions(self):
        if self.connected:
            return self.kite.positions()
        return {"error": "Not connected"}
