from core.gmail import authentificate, read_email

def process_email(body):
    print(body)
    return body

if __name__ == "__main__":
    credentials = authentificate()
    read_email(credentials, 'hello_sliver_0@icloud.com', process_email)