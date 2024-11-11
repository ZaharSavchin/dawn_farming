import aiohttp
from data.config import API_KEY

async def solve_captcha(base64_image: str) -> str | None:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    payload = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Which characters are on this image? Look for black characters only ignoring grey. Read characters strictly from left to right, they are placed on a single line. Characters are case-sensitive, look out for the size of each character relative to others and for the typeface of character. The answer should match ^[A-Za-z0-9@#$&=]{6}$ regular expression. Answer with the string only."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 500
    }

    async with aiohttp.ClientSession() as session:
        async with session.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload) as response:
            if response.status == 200:
                result = await response.json()
                answer = result['choices'][0]['message']['content'] if 'choices' in result else ''
                phrase = ' are: '
                start = answer.index(phrase) + len(phrase) if phrase in answer else 0
                symbols = answer[start:]
                result = symbols.replace(',', '').replace(' ', '').replace('.', '').replace('*', '')
                print('Captcha answer:', result)
                return result
            else:
                print('Request failed. Status: ' + str(response.status))
                print(await response.text())
                return None
