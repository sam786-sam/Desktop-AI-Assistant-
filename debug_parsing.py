prompt = 'send message to john saying hello'
prompt_lower = prompt.lower().strip()
print('prompt_lower:', repr(prompt_lower))

func = 'whatsapp'
patterns = ['whatsapp', 'whats app', 'send message']
print('patterns:', patterns)

for pattern in patterns:
    print(f'  {repr(pattern)} in prompt: {pattern in prompt_lower}')
    
# Check which pattern matches
for pattern in patterns:
    if pattern in prompt_lower:
        print(f'Matched pattern: {repr(pattern)}')
        remaining = prompt_lower.replace(pattern, '', 1).strip()
        print(f'Remaining after replace: {repr(remaining)}')
        break