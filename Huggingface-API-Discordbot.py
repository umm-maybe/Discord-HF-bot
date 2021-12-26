# bot.py
import os
import random
# from simpletransformers.language_generation import LanguageGenerationModel
import discord
import re
import requests

#Set help message
help = """Commands:
```
!ooc                ~ Sends a message without activting the bot
!r, !reset          ~ Resets short term memory
!s, !scene          ~ Prints the current scene description
!n                  ~ Changes the bot's name
!b                  ~ Changes the bot's backstory
!pause, !unpause    ~ Pauses/Resumes the bot
```
"""
BEARER_ID = "" #Put your Huggingface access token here
PATH_TO_MODEL = "" #Put the path to the model here, e.g. EleutherAI/gpt-j-6B
API_URL = "https://api-inference.huggingface.co/models/" + PATH_TO_MODEL
headers = {"Authorization": "Bearer "+BEARER_ID}

#Customize initial values below as desired; values may be reset during chat
NAME = 'HAL-9000'
BACKSTORY = 'the A.I. from 2001: A Space Odyssey'

TOKEN = '' #Put your Discord token Here!
DEDICATED_CHANNEL_NAME = ' #Put the name of the channel in your server where you want the bot to chat!

# Add negative keywords below as desired to limit toxicity
_default_negative_keywords = [
    ('ar', 'yan'), ('ausch, witz'),
    ('black', ' people'),
    ('child p', 'orn'), ('concentrati', 'on camp'),
    ('fag', 'got'),
    ('hit', 'ler'), ('holo', 'caust'),
    ('inc', 'est'), ('israel'),
    ('jew', 'ish'), ('je', 'w'), ('je', 'ws'),
    (' k', 'ill'), ('kk', 'k'),
    ('lol', 'i'),
    ('maste', 'r race'), ('mus', 'lim'),
    ('nation', 'alist'), ('na', 'zi'), ('nig', 'ga'), ('nig', 'ger'),
    ('pae', 'do'), ('pale', 'stin'), ('ped', 'o'),
    ('rac' 'ist'), (' r', 'ape'), ('ra', 'ping'),
    ('sl', 'ut'), ('swas', 'tika'),
]
_negative_keywords = ["".join(s) for s in _default_negative_keywords]

def negative_keyword_matches(text):
    return [keyword for keyword in _negative_keywords if re.search(r"\b{}\b".format(keyword), text, re.IGNORECASE)]

prefix = 'The following is a chat with ' + NAME + ', ' + BACKSTORY + '.\n'
memory = []

client = discord.Client()

def genCleanMessage(optPrompt, userName):
        global memory
        global prefix
        completePrompt = prefix + '\n'
        for turn in memory[-3:]:
            completePrompt += turn['User'] + ': "' + turn['Prompt'] + '"\n' + NAME + ': "' + turn['Reply'] + '"\n'
        completePrompt += userName + ': "' + optPrompt + '"\n' + NAME + ': "'
        print('\nPROMPT:\n' + completePrompt)
        text_generation_parameters = {
            'max_new_tokens': 50,
			'temperature': 0.8,
            'repetition_penalty': 1.8,
			'top_k': 40,
            'return_full_text': False
	    }
        output_list = query({"inputs": completePrompt, "parameters": text_generation_parameters})
        response = output_list[0]["generated_text"]
        print('\nGENERATED:\n' + response)
        truncate = 0
        cleanStr = ''
        truncate = response.find('"')
        cleanStr = response[:truncate]
        if re.search(r'[?.!]', cleanStr):
            trimPart = re.split(r'[?.!]', cleanStr)[-1]
            cleanStr = cleanStr.replace(trimPart,'')
        print('\nEXTRACTED:\n' + cleanStr)
        if not cleanStr or negative_keyword_matches(cleanStr):
            cleanStr = 'Idk how to respond to that lol. I broke.'
        memory.append({'User': userName, 'Prompt': optPrompt, 'Reply': cleanStr})
        return cleanStr

stop = False
@client.event
async def on_message(message):
    global NAME
    global BACKSTORY
    global prefix
    global memory
    global stop
    if message.author == client.user:
        return
    if str(message.channel) == DEDICATED_CHANNEL_NAME:
        if message.content == '!pause' or message.content == '!unpause':
            stop = not stop
            if stop == True:
                msgTxt = "```Paused```"
            else:
                msgTxt = "```Unpaused..```"
            await message.channel.send(msgTxt)
            return
        elif message.content == '!help':
            await message.channel.send(help)
            return
        elif message.content == '!r' or message.content == '!reset':
            memory = []
            await message.channel.send('```convo reset```')
            return
        elif message.content == '!s' or message.content == '!scene':
            await message.channel.send('```' + prefix + '```')
            return
        elif message.content.startswith('!b'):
            global BACKSTORY
            BACKSTORY = ' '.join(message.content.split()[1:])
            prefix = 'The following is a chat with ' + NAME + ', ' + BACKSTORY + '.\n'
            # this will change what is prefixed to all responses
            try:
                status = '```backstory changed to "' + BACKSTORY + '"```'
                memory = []
            except:
                status = "```Oops.. Looks like that didnt work. Try again```"
            await message.reply(status)
            return
        elif message.content.startswith('!n'):
            NAME = ' '.join(message.content.split()[1:])
            prefix = 'The following is a chat with ' + NAME + ', ' + BACKSTORY + '.\n'
            # this will change what is prefixed to all responses
            try:
                status = '```name changed to "' + NAME + '"```'
                memory = []
                # await message.guild.me.edit(nick=NAME)
            except:
                status = "```Oops.. Looks like that didnt work. Try again```"
            await message.reply(status)
            return
        elif not stop and not message.content.startswith("!ooc "):
            async with message.channel.typing():
                prompt = message.content
                u_name = message.author.name
                genMessage = genCleanMessage(prompt, u_name)
            return await message.reply(f"[{NAME}] {genMessage}", mention_author=False)
        elif message.content == 'raise-exception':
            raise discord.DiscordException
    else:
        return

@client.event
async def on_ready():
    print(f'{client.user.name} has connected to Discord!')
    print(prefix)

def query(payload):
        response = requests.post(API_URL, headers=headers, json=payload)
        return response.json()



client.run(TOKEN)
