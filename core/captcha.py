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
                        "text": "What symbols (6 bold) are shown on the image? Please return/tell me ONLY symbols without any other text."
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
