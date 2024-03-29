#!/usr/bin/env python3

import discord
import types
import sys
from urllib.parse import urlparse

def _uri_validate(x):
    try:
        result = urlparse(x)
        return all([result.scheme, result.netloc])
    except:
        return False

class DiscordSHContestBot:
    _intents = discord.Intents.default()
    _intents.message_content = True
    _client = discord.Client(intents=_intents)

    '''
    @param prefix the prefix that precede commands processed by the bot
    @param log_func the function for the bot to write logs with
    @param work_guild_ids ids of the guilds that the bot works with
    '''
    def __init__(self, prefix='!', *, log_func=None, work_guild_ids=None, submissions_filepath=None):
        self.prefix = prefix
        self.log_func = log_func
        self.work_guild_ids = work_guild_ids
        self._submissions = None
        self._submissions_filepath = submissions_filepath

        @self._client.event
        async def on_ready():
            self._log(f"Logged in as {self._client.user}")
            if self._submissions is None:
                self._submissions = []
                if self._submissions_filepath is not None:
                    await self._read_submissions_file()
            await self._client.change_presence(activity=discord.Game("!help"))

        @self._client.event
        async def on_message(msg):
            if not msg.content.lstrip().startswith(prefix):
                return
            if (self.work_guild_ids is not None):
                if ((msg.guild.id if (msg.guild is not None) else None) not in self.work_guild_ids):
                    return
            await self._process_command(msg, msg.content.lstrip()[len(self.prefix):].split())

    '''
    Run the bot
    @param bot token
    '''
    def run(self, token=None):
        self._client.run(token)

    def _write_submissions_file(self):
        with open(self._submissions_filepath, 'w') as f:
            f.write('\n'.join([f'{submission["author"].id}:{submission["link"]}' for submission in self._submissions]))

    async def _read_submissions_file(self):
        with open(self._submissions_filepath, 'r') as f:
            for line in f:
                sep_pos = line.find(':')
                author = int(line[:sep_pos])
                link = line[sep_pos+1:].removesuffix('\n')
                self._submissions.append({'author': await self._client.fetch_user(author), 'link': link})

    def _check_in_submission(self, author, submission):
        for i in range(len(self._submissions)):
            if self._submissions[i]['author'] != author:
                continue
            self._submissions[i]['link'] = submission
            return
        self._submissions.append({'author': author, 'link': submission})
        self._write_submissions_file()

    async def _process_command(self, msg, args):
        async def _response(content):
            await msg.reply(content, mention_author=False)

        if args[0] == 'ping':
            await _response('pong')

        elif args[0] == 'submit':
            submission_link = msg.content[len({self.prefix})+len(args[0]):].strip()
            if submission_link.startswith('<') and submission_link.endswith('>'):
                submission_link = submission_link[1:-1]
            if (len(args) < 2) or (not _uri_validate(submission_link)):
                await _response('Couldn\'t make a submission\n'
                                'Please, provide a link to your submission\n'
                                f'Example: `{self.prefix}submit https://github.com/knot126/KSAM-Assets`')
                return
            self._check_in_submission(msg.author, submission_link)
            await _response(f'Submitted <{submission_link}> successfully')

        elif args[0] == 'unsubmit':
            for i in range(len(self._submissions)):
                if self._submissions[i]['author'] != msg.author:
                    continue
                del self._submissions[i]
                self._write_submissions_file()
                await _response('Your submission was removed successfully')
                return
            await _response('You have not submitted anything')

        elif args[0] == 'submissions':
            if len(self._submissions) == 0:
                await _response('No submissions were made so far')
                return
            text = '\n'.join([ f'`@{i["author"].name}`:  <{i["link"]}>' for i in self._submissions ])
            await _response(text)

        elif args[0] == 'help':
            await _response(f'`{self.prefix}submit <link>` - make/remake a submission\n'
                            f'`{self.prefix}unsubmit` - remove your submission\n'
                            f'`{self.prefix}submissions` - view all submissions made so far')

    def _log(self, *args):
        if callable(self.log_func):
            self.log_func(*args)
