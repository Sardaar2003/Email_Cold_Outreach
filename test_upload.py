import pandas as pd
import requests

# 1. Create a dummy excel file with some valid and some invalid emails
data = [
    {"First Name": "Alice", "Last Name": "Smith", "Email": "alice@example.com"},
    {"First Name": "Bob", "Last Name": "Jones", "Email": "not-an-email"},
    {"First Name": "Charlie", "Last Name": "Brown", "Email": "charlie@gmail.com"},
    {"First Name": "Dave", "Last Name": "White", "Email": "dave@"},
    {"First Name": "Eve", "Last Name": "Black", "Email": ""}
]

df = pd.DataFrame(data)
df.to_excel("test_upload.xlsx", index=False)

print("Created test_upload.xlsx")
