import threading
import time
import discord
from discord import Webhook, RequestsWebhookAdapter
import config


def remove_mentions(text):
    new_text = text
    try:
        i = 0
        while i < len(new_text):
            if new_text[i] == '<' and i + 1 < len(new_text) and (new_text[i + 1] == '!' or new_text[i + 1] == '@'):
                for j in range(i, len(new_text), 1):
                    if new_text[j] == '>':
                        new_text = new_text[:i] + new_text[j + 1:]
                        break
            i += 1

        return new_text.replace('   ', ' ').replace('  ', ' ')
    except Exception as e:
        return text


def remove_emojis(text):
    # Replace custom animated emojis
    new_text = text
    try:
        i = 0
        while i < len(new_text):
            if new_text[i] == '<' and i + 2 < len(new_text) and new_text[i + 1] == 'a' and new_text[i + 2] == ':':
                for j in range(i, len(new_text), 1):
                    if new_text[j] == '>':
                        new_text = new_text[:i] + new_text[j + 1:]
                        break
            i += 1

        new_text = new_text.replace('   ', ' ').replace('  ', ' ')
    except Exception as e:
        pass

    # Replace custom emojis
    try:
        i = 0
        while i < len(new_text):
            if new_text[i] == '<' and i + 1 < len(new_text) and new_text[i + 1] == ':':
                for j in range(i, len(new_text), 1):
                    if new_text[j] == '>':
                        new_text = new_text[:i] + new_text[j + 1:]
                        break
            i += 1

        new_text = new_text.replace('   ', ' ').replace('  ', ' ')
    except Exception as e:
        pass

    # Replace failed emojis
    try:
        i = 0
        while i < len(new_text):
            if new_text[i] == ':' and i + 1 < len(new_text) and new_text[i + 1] != ' ' and new_text[i + 1] != '/':
                for j in range(i + 1, len(new_text), 1):
                    if new_text[j] == ':':
                        new_text = new_text[:i] + new_text[j + 1:]
                        break
            i += 1

        return new_text.replace('   ', ' ').replace('  ', ' ')
    except Exception as e:
        return text


def scan_channel_webhooks():
    global channels_webhooks

    while True:
        new_channels_webhooks = {}

        with open(config.channels_webhooks_file_path, "r") as file:
            lines = file.readlines()
            lines = [line.rstrip() for line in lines]

        for line in lines:
            if ' ' not in line or line == "" or line == "\n":
                continue

            if line.endswith('\r'):
                line = line[:-2]

            splits = line.split(" ")
            channel = splits[0]
            webhook = splits[1]
            if channel not in new_channels_webhooks.keys():
                new_channels_webhooks[channel] = []
            new_channels_webhooks[channel].append(webhook)

        channels_webhooks = new_channels_webhooks
        time.sleep(config.scan_interval_seconds)


thread = threading.Thread(target=scan_channel_webhooks, args=())
thread.start()


class Bot(discord.Client):
    async def on_ready(self):
        print(f"Forwarding bot started. Logged in as {self.user.name}#{self.user.discriminator}")

    async def on_message(self, message):
        if str(message.channel.id) in channels_webhooks.keys():
            for webhook_url in channels_webhooks[str(message.channel.id)]:
                webhook = Webhook.from_url(webhook_url, adapter=RequestsWebhookAdapter())

                if config.webhook_username != "":
                    username = config.webhook_username
                else:
                    username = f"{message.author.name}#{message.author.discriminator}"

                if config.webhook_profile_picture_URL != "":
                    avatar_url = config.webhook_profile_picture_URL
                else:
                    avatar_url = message.author.avatar_url

                try:
                    if config.show_replied_to_messages and message.reference:
                        if config.remove_custom_emojis:
                            content = remove_emojis(message.reference.resolved.content)
                        else:
                            content = message.reference.resolved.content

                        if config.remove_mentions:
                            content = remove_mentions(content)

                        text = f"(**in reply to {message.reference.resolved.author.name}#{message.reference.resolved.author.discriminator}:** {content.strip()})"
                        webhook.send(text, username=username, avatar_url=avatar_url)
                except Exception as e:
                    pass

                if message.content and message.content != "":
                    try:
                        if config.remove_custom_emojis:
                            text = remove_emojis(message.content)
                        else:
                            text = message.content

                        if config.remove_mentions:
                            text = remove_mentions(text)

                        webhook.send(text.strip(), username=username, avatar_url=avatar_url)
                    except Exception as e:
                        pass

                if len(message.attachments) > 0:
                    for attachment in message.attachments:
                        try:
                            webhook.send(attachment.url, username=username, avatar_url=avatar_url)
                        except Exception as e:
                            pass

                if len(message.embeds) > 0:
                    for i in range(len(message.embeds)):
                        try:
                            if message.embeds[i].type == "rich":
                                webhook.send(embed=message.embeds[i], username=username, avatar_url=avatar_url)
                        except Exception as e:
                            pass


bot = Bot()
bot.run(config.token)
