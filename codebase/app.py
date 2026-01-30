"""
Example buggy application for testing the multi-agent RCA system.
This file contains a NoneType error.
"""

class DataProcessor:
    def __init__(self, value):
        self.value = value
    
    def process(self):
        return self.value * 2

def fetch_data(source):
    """
    Fetch data from source.
    Returns None if source is invalid.
    """
    if source == "valid":
        return DataProcessor(10)
    else:
        return None

def main():
    """
    Main function that processes data.
    BUG: No null check before calling process()
    """
    source = "invalid"  # This will cause data to be None
    data = fetch_data(source)
    
    # BUG: Should check if data is None before calling process()
    result = data.process()  # AttributeError: 'NoneType' object has no attribute 'process'
    
    print(f"Result: {result}")

if __name__ == "__main__":
    main()
