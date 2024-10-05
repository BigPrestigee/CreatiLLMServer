import os 
from vllm.sampling_params import SamplingParams
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response, StreamingResponse
import uvicorn
from utils_wrapper import _build_prompt,remove_stop_words, load_vllm
import uuid
import json 

app=FastAPI()

# load vllm
generation_config,tokenizer,stop_words_ids,engine=load_vllm()

@app.post("/chat")
async def chat(request: Request):
    request=await request.json()
    
    query=request.get('query',None)
    history=request.get('history',[])
    system=request.get('system','You are a helpful assistant.')
    stream=request.get("stream",False)
    user_stop_words=request.get("user_stop_words",[])

    if query == "":
        text = "你好,请问你想问点什么呢?"
        ret={"text":text}
        return JSONResponse(ret)

    user_stop_tokens=[]
    for words in user_stop_words:
        user_stop_tokens.append(tokenizer.encode(words))
    

    prompt_text,prompt_tokens=_build_prompt(generation_config,tokenizer,query,history=history,system=system)
        
    sampling_params=SamplingParams(stop_token_ids=stop_words_ids, 
                                    early_stopping=False,
                                    top_p=generation_config.top_p,
                                    top_k=-1 if generation_config.top_k == 0 else generation_config.top_k,
                                    temperature=generation_config.temperature,
                                    repetition_penalty=generation_config.repetition_penalty,
                                    max_tokens=generation_config.max_new_tokens)

    request_id=str(uuid.uuid4().hex)
    results_iter=engine.generate(prompt=None,sampling_params=sampling_params,prompt_token_ids=prompt_tokens,request_id=request_id)
    
    def match_user_stop_words(response_token_ids,user_stop_tokens):
        for stop_tokens in user_stop_tokens:
            if len(response_token_ids)<len(stop_tokens):
                continue 
            if response_token_ids[-len(stop_tokens):]==stop_tokens:
                return True
        return False

    if stream:
        async def streaming_resp():
            async for result in results_iter:
                token_ids=remove_stop_words(result.outputs[0].token_ids,stop_words_ids)               
                text=tokenizer.decode(token_ids)
                yield (json.dumps({'text':text})+'\0').encode('utf-8')
                if match_user_stop_words(token_ids,user_stop_tokens):
                    await engine.abort(request_id)
                    break
        return StreamingResponse(streaming_resp())

    # non-stream
    async for result in results_iter:
        token_ids=remove_stop_words(result.outputs[0].token_ids,stop_words_ids)              
        text=tokenizer.decode(token_ids)
        if match_user_stop_words(token_ids,user_stop_tokens):
            await engine.abort(request_id)
            break

    ret={"text":text}
    return JSONResponse(ret)

if __name__=='__main__':
    uvicorn.run(app,host=None,port=8000,log_level="debug")