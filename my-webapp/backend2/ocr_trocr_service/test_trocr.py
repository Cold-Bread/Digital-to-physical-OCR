# test_trocr.py
import requests

with open(r"C:\Users\Jacob\Downloads\imagetest.jpg", "rb") as f:
    files = {"file": f}
    response = requests.post("http://localhost:8001/trocr/ocr", files=files)
    print(response.json())