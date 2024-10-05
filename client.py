import requests
import json

def chat_api(query,history):
    response=requests.post('http://localhost:8000/chat',json={
        'query':query,
        'stream': True,
        'history':history
    },stream=True)
    
    for chunk in response.iter_lines(chunk_size=8192,decode_unicode=False,delimiter=b"\0"):
        if chunk:
            data=json.loads(chunk.decode('utf-8'))
            text=data["text"].rstrip('\r\n')
            yield text

if __name__ == '__main__':
    
    history=[]
    
    while True:
        query=input('提问:')
        last_text = None
        # iterator generator
        for text in chat_api(query, history):
            print('\033[2J')
            print(text)
            last_text = text
        history.append((query, last_text))
        history = history[-10:]

