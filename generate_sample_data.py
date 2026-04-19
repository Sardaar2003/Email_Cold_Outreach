import pandas as pd
import os

data = {
    'First Name': ['John', 'Jane', 'Michael', 'Sarah'],
    'Middle Name': ['M.', 'A.', 'J.', 'L.'],
    'Last Name': ['Doe', 'Smith', 'Johnson', 'Williams'],
    'Title': ['CEO', 'Marketing Director', 'CTO', 'Operations Manager'],
    'Company Name': ['TechFlow', 'CreativePulse', 'NextGen AI', 'Global Logistics'],
    'Mailing Address': ['123 Tech Lane', '456 Design St', '789 Innovation Dr', '101 Supply Rd'],
    'Primary City': ['San Francisco', 'New York', 'Austin', 'Chicago'],
    'Primary State': ['CA', 'NY', 'TX', 'IL'],
    'ZIP Code': ['94105', '10001', '78701', '60601'],
    'Country': ['USA', 'USA', 'USA', 'USA'],
    'Phone': ['555-0101', '555-0102', '555-0103', '555-0104'],
    'Web Address': ['techflow.com', 'creativepulse.io', 'nextgen.ai', 'globallogistics.com'],
    'Email': ['john@example.com', 'jane@example.com', 'michael@example.com', 'sarah@example.com'],
    'Revenue': ['5000000', '10000000', '2000000', '50000000'],
    'Employee': ['50', '120', '15', '500'],
    'Industry': ['Software', 'Marketing', 'Artificial Intelligence', 'Logistics'],
    'Sub Industry': ['SaaS', 'Digital Agency', 'Machine Learning', 'Freight']
}

try:
    df = pd.DataFrame(data)
    os.makedirs('data', exist_ok=True)
    df.to_excel('data/leads_sample.xlsx', index=False)
except Exception as e:
    # Minimal fallback in case of env issues
    with open('data/status.txt', 'w') as f:
        f.write(f"Error: {str(e)}")
