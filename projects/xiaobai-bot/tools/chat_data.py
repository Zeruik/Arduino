"""Encode alternating chat pairs with assistant-only labels (legacy QA compatible)."""
def encode_row(tok,row):
    if 'messages' in row:
        messages=row['messages']
        if not messages or len(messages)%2:
            raise ValueError('messages must contain complete user/assistant pairs')
        pairs=[]
        for i in range(0,len(messages),2):
            u,a=messages[i:i+2]
            if u['role']!='user' or a['role']!='assistant':
                raise ValueError('roles must alternate user/assistant')
            pairs.append((u['content'],a['content']))
    else:pairs=[(row['question'],row['answer'])]
    ids=[];labels=[]
    for i,(question,answer) in enumerate(pairs):
        prefix=tok.encode(f'<|im_start|>user\n{question}<|im_end|>\n<|im_start|>assistant\n',add_special_tokens=False)
        tail=tok.encode(answer+'<|im_end|>\n',add_special_tokens=False)
        ids+=prefix+tail
        supervise=not row.get('loss_last_only',False) or i==len(pairs)-1
        labels += [-100]*len(prefix)+(tail if supervise else [-100]*len(tail))
    return ids,labels
