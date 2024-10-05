import gradio as gr
import requests
import json
from client import chat_api

with open('config.json', 'r') as f:
    config = json.load(f)

max_history = config['max_history']

js = """
function createGradioAnimation() {
    var container = document.createElement('div');
    container.id = 'gradio-animation';
    container.style.fontSize = '4em';
    container.style.fontWeight = 'bold';
    container.style.textAlign = 'left';
    container.style.marginBottom = '20px';

    var text = 'Welcome to Qwen-1.8B-Chat Bot👾!';
    for (var i = 0; i < text.length; i++) {
        (function(i){
            setTimeout(function(){
                var letter = document.createElement('span');
                letter.style.opacity = '0';
                letter.style.transition = 'opacity 0.5s';
                letter.innerText = text[i];

                container.appendChild(letter);

                setTimeout(function() {
                    letter.style.opacity = '1';
                }, 50);
            }, i * 250);
        })(i);
    }

    var gradioContainer = document.querySelector('.gradio-container');
    gradioContainer.insertBefore(container, gradioContainer.firstChild);

    return 'Animation created';
}
"""

css = """
.custom-shadow {
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    border-radius: 8px;
    padding: 10px;
}
"""
# 调用chat_streaming函数并将结果返回给chatbot
def chat(query, history):
    for response in chat_api(query,history):
        yield '', history+[(query,response)]
    history.append((query,response))
    # print("对话历史:", history)
    while len(history) > max_history:
        history.pop(0)

with gr.Blocks(css=css, js=js) as app:

    with gr.Row():
        chatbot = gr.Chatbot(label="历史聊天")
    
    with gr.Row():
        query_box = gr.Textbox(label="输入框", autofocus=True, lines=3, placeholder="你可以尝试问 : 1+1=?", elem_id="query_box")
    
    with gr.Row():
        submit_btn = gr.Button(value='提交', elem_classes="custom-shadow")
    
    submit_btn.click(chat, [query_box, chatbot], [query_box, chatbot])
    
if __name__ == "__main__":
    # gradio server config
    app.queue(40)
    app.launch(server_name='0.0.0.0',max_threads=80)