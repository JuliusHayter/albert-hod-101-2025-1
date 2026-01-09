import os
from pathlib import Path
import time
import requests
import re
import urllib.parse
from slack_sdk import WebClient

slack_bot_token = os.getenv('SLACK_BOT_TOKEN')
general_channel = os.getenv('GENERAL_CHANNEL')
our_channel = os.getenv('OUR_CHANNEL')
slack_client_id = os.getenv('SLACK_CLIENT_ID')

client = WebClient(token=slack_bot_token)

redirect_url = f"https://slack.com/oauth/v2/authorize?scope=chat:write:bot&client_id={slack_client_id}"


def send_message(message):
    response = client.chat_postMessage(channel=our_channel,text=message)
    return response


def upload_images(images_dir_path='images'):
    images_dir = Path('.') / images_dir_path
    
    for p in images_dir.iterdir():
        r = client.files_getUploadURLExternal(filename=p.name, length=p.stat().st_size)
        upload_url = r["upload_url"]
        file_id = r["file_id"]

        with p.open("rb") as f:
            requests.post(upload_url, files={"file": (p.name, f)})

        client.files_completeUploadExternal(
            channel_id=our_channel,
            files=[{"id": file_id, "title": p.name}],
        )


def get_wikipedia_first_paragraph(title):
    url_title = title.replace(' ', '_')
    encoded_title = urllib.parse.quote(url_title, safe='')
    headers = {'User-Agent': 'SlackBot/1.0 (https://slack.com; contact@example.com)'}
    
    for lang in ['fr', 'en']:
        try:
            url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{encoded_title}"
            response = requests.get(url, headers=headers, timeout=5)
            
            if response.status_code == 404:
                continue
            
            response.raise_for_status()
            data = response.json()
            
            if 'extract' in data and data['extract']:
                extract = data['extract']
                first_paragraph = extract.split('\n')[0]
                if len(first_paragraph) > 500:
                    sentences = first_paragraph.split('. ')
                    if len(sentences) > 0:
                        return sentences[0] + '.'
                return first_paragraph
            elif 'description' in data and data['description']:
                return data['description']
        except requests.exceptions.Timeout:
            if lang == 'en':
                print(f"Timeout pour: {title}")
            continue
        except requests.exceptions.RequestException as e:
            if lang == 'en':
                print(f"Erreur: {e}")
            continue
        except Exception as e:
            if lang == 'en':
                print(f"Erreur inattendue: {e}")
            continue
    
    return None


def listen_and_respond():
    processed_messages = set()
    bot_user_id = client.auth_test().get('user_id', '')
    
    print("start")
    
    while True:
        try:
            result = client.conversations_history(channel=our_channel, limit=10)
            
            if result["ok"]:
                for message in result["messages"]:
                    if 'bot_id' in message or message.get('user') == bot_user_id:
                        continue
                    
                    text = message.get('text', '')
                    match = re.match(r'^Wikipedia:\s*(.+)$', text, re.IGNORECASE)
                    
                    if match:
                        message_id = f"{message.get('ts', '')}:{text}"
                        
                        if message_id not in processed_messages:
                            processed_messages.add(message_id)
                            title = match.group(1).strip()
                            print(f"Message trouvé: Wikipedia:{title}")
                            
                            paragraph = get_wikipedia_first_paragraph(title)
                            
                            if paragraph:
                                client.chat_postMessage(
                                    channel=our_channel,
                                    text=f"*{title}*\n\n{paragraph}"
                                )
                                print(f"good pour: {title}")
                            else:
                                client.chat_postMessage(
                                    channel=our_channel,
                                    text=f"ça marche pas pour '{title}' :("
                                )
                                print(f"Erreur pour {title}")
            
            time.sleep(2)
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Erreur {e}")
            time.sleep(5)


if __name__ == "__main__":
    listen_and_respond()

