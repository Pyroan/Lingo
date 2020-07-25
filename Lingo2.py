import discord
import asyncio
from discord.ext.commands import Bot
from discord.ext import commands
from discord.utils import find
import platform
import logging

import os
import csv
import configparser
import re
from random import randint

# Bad hack to keep this alive even though discord tried to kill it


class Overwrites:
    __slots__ = ('id', 'allow', 'deny', 'type')

    def __init__(self, **kwargs):
        self.id = kwargs.pop('id')
        self.allow = kwargs.pop('allow', 0)
        self.deny = kwargs.pop('deny', 0)
        self.type = kwargs.pop('type')

    def _asdict(self):
        return {
            'id': self.id,
            'allow': self.allow,
            'deny': self.deny,
            'type': self.type,
        }


logging.basicConfig(level=logging.INFO)
# Here you can modify the bot's prefix and description and whether it sends help in direct messages or not.
client = Bot(description="Lingo 2 by Pyroan!",
             command_prefix=("L!", "!", "l!"), pm_help=True)

# Set up configuration
dev_id = 'Error'
token = 'Error'
is_production = os.environ['IS_HEROKU']
if is_production:
    dev_id = os.environ['DEV_ID']
    token = os.environ['TOKEN']
else:
    settings = configparser.RawConfigParser()
    settings.read('config.cfg')
    # Developer's ID
    dev_id = settings.get('Settings', 'dev_id')
    # Bot token
    token = settings.get('Settings', 'token')

# Set up nationality and language lists
nationalities = []
languages = []
proficiencies = ["fluent", "conversational", "learning"]


def init_nationalities():
    global nationalities
    nationalities = []
    with open('data/nationalities.csv', 'r') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            new = dict()
            new['country'] = row[0]
            new['demonym'] = row[1]
            new['aliases'] = []
            for alias in row:
                if alias != '':
                    new['aliases'].append(alias)
            nationalities.append(new)
        print("LINGO: %d Nationalities loaded successfully" %
              len(nationalities))


def init_languages():
    global languages
    languages = []
    with open('data/iso_languages.csv', 'r') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            new = dict()
            new['iso_639'] = row[0]
            new['iso_639_2'] = row[1]
            new['iso_639_2B'] = row[2]
            new['aliases'] = []
            for alias in row:
                if alias != '':
                    new['aliases'].append(alias)
            new['name'] = row[3]
            languages.append(new)
        print("LINGO: %d Languages loaded sucessfully" % len(languages))


# This is what happens everytime the bot launches. In this case, it prints information
# like server count, user count the bot is connected to, and the bot id in the console.
# Additionally, calls setup functions
@client.event
async def on_ready():
    # print('Logged in as ' + client.user.name + ' (ID:' + str(client.user.id) + ') | Connected to ' +
    #    str(len(client.servers)) + ' servers | Connected to ' + str(len(set(client.get_all_members()))) + ' users')
    # print('--------')
    # print('Current Discord.py Version: {} | Current Python Version: {}'.format(discord.__version__,
    #                                                                           platform.python_version()))
    print('--------')
    print('Use this link to invite {}:'.format(client.user.name))
    print('https://discordapp.com/oauth2/authorize?client_id={}&scope=bot&permissions=8'.format(client.user.id))
    print('--------')
    init_nationalities()
    init_languages()


###########################
#      USER COMMANDS      #
###########################

# This is a basic example of a call and response command. You tell it do "this" and it does it.
@client.command(hidden=True)
async def ping(ctx):
    await ctx.send(":thumbsup: Yep, I'm awake!")


# Mostly a test command. Rolls a die of given size
@client.command()
async def roll(ctx, *args):
    try:
        size = 20
        if len(args) > 0:
            arg = args[0]
            if arg[0] == 'd':
                arg = arg[1:]
            size = int(arg)
            if size <= 0:
                await ctx.send("Size must be bigger than 0!")
                return

        await ctx.send(":game_die: Result of d%d roll: %d" % (size, randint(1, size)))
    except ValueError:
        await ctx.send("Correct Usage: `L!roll <size>`")


# Output a nicely formatted table of the given list
@client.command(name="list")
async def list_all(ctx, ls=None):
    if ls is None or ls not in ['nationalities', 'languages']:
        await ctx.send("Usage: `L!list [nationalities|languages]`")
    else:
        lis = []
        field = ''
        if ls == 'nationalities':
            for entry in nationalities:
                lis.append(entry['country'])
                field = 'country'
        elif ls == 'languages':
            for entry in languages:
                lis.append(entry['name'])
                field = 'language'
        output = ["Available {}:\n```\n".format(ls)]
        if len(lis) % 2 == 1:
            lis.append('')
        for i in range(0, len(lis), 2):
            output.append("{:<20}{:<20}\n".format(lis[i], lis[i+1]))
        output.append("```\nNot seeing the {} you're looking for? "
                      "Ask a moderator to have it added!".format(field))
        await ctx.send(''.join(output))


# Given an ISO code or language, prints out the languages name and ISO codes
# If a query matches multiple languages, they'll all be printed.
@client.command(aliases=["whatis", "iso", "search"])
async def lookup(ctx, *, query=None):
    if query is None:
        await ctx.send("Usage: `L!lookup <query>`")
        return
    found = {'exact': [], 'other': []}
    # Find ALL languages that match the query
    matcher = re.compile(query, re.IGNORECASE)
    for entry in languages:
        for alias in entry['aliases']:
            if matcher.fullmatch(alias):
                found['exact'].append(entry)
                break
            elif matcher.search(alias):
                found['other'].append(entry)
                break
    if len(found) == 0:
        await ctx.send("No languages found for `{}`\n"
                       "For a list of available languages, try `L!list languages`".format(query))
    else:
        output = ["Matching languages:\n```\n"]
        output.append("{:<16}{:<9}\n".format("Language", "ISO Codes"))
        output.append("-" * 32)
        output.append("\n")
        for entry in found['exact']:
            output.append("{:<16}{:<5}{:<5}{:<5}\n".format(entry['name'], entry['iso_639'],
                                                           entry['iso_639_2'], entry['iso_639_2B']))
        if len(found['exact']) != 0 and len(found['other']) != 0:
            output.append("-"*32)
            output.append("\n")
        for entry in found['other']:
            output.append("{:<16}{:<5}{:<5}{:<5}\n".format(entry['name'], entry['iso_639'],
                                                           entry['iso_639_2'], entry['iso_639_2B']))
        output.append("```")
        await ctx.send(''.join(output))


# Set/Remove nationality roles
@client.command(aliases=["country"], pass_context=True)
async def nationality(ctx, *, country=None):
    if country is None:
        await ctx.send("Usage: `L!nationality <country>`\n"
                       "For a list of available countries, try `L!list nationalities`")
    else:
        # Find the target demonym
        user = ctx.message.author
        country_role = None
        matcher = re.compile(country, re.IGNORECASE)
        for entry in nationalities:
            if country_role is not None:
                break
            for alias in entry['aliases']:
                if matcher.fullmatch(alias):
                    country_role = entry['demonym']
        if country_role is None:
            await ctx.send("Couldn't find country: `%s`.\n"
                           "If you're sure you didn't make a mistake, please contact a moderator.\n"
                           "(It probably just needs to be added to the list)" % (country))
        else:
            new_role = find(lambda r: r.name == country_role,
                            ctx.message.guild.roles)
            if new_role is not None:
                # Remove any current nationality roles
                for role in user.roles:
                    if role.name in list(map(lambda x: x['demonym'], nationalities)):
                        await user.remove_roles(role)
                # Actually add the role.
                await user.add_roles(new_role)
                await ctx.send("Set %s's nationality to %s" % (user.mention, country_role))
            else:
                await ctx.send("No server role found for `%s`. Nationality unchanged\n"
                               "(Ask a moderator to add the role and try again)" % country_role)


# Sets "Verified" role, for users that wish to have a role but don't want to reveal their nationality
@client.command(pass_context=True)
async def verify(ctx):
    user = ctx.message.author
    role = find(lambda r: r.name == "Verified", ctx.message.guild.roles)
    if role is not None:
        if role in user.roles:
            await ctx.send("You're already verified!")
        else:
            await user.add_roles(role)
            await ctx.send(":tada: %s is now verified. Welcome!" % user.mention)
    else:
        await ctx.send("This server has no \"Verified\" role. :frowning:")


# Functions for adding/removing/setting language roles
@client.group(aliases=["language"], pass_context=True)
async def lang(ctx):
    if ctx.invoked_subcommand is None:
        await ctx.send("Usage: `L!lang [add|remove] [fluent|conversational|learning] <language name | ISO639 code>`\n"
                       "For a list of available languages, try `L!list languages`")


# Helper function to construct a language role string
# Used for !lang add and !lang remove.
async def find_language_role(ctx, proficiency, language):
    matcher = re.compile(language, re.IGNORECASE)
    new_role_name = None
    # Find target ISO code
    for entry in languages:
        for alias in entry['aliases']:
            if new_role_name is not None:
                break
            if matcher.fullmatch(alias):
                if entry['iso_639'] != '':
                    new_role_name = entry['iso_639']
                else:
                    new_role_name = entry['iso_639_2']
    if new_role_name is None:
        await ctx.send("Language not found: %s\n"
                       "For a list of available languages, try `L!list languages`" % language)
        return
    # Format proficiency
    brackets = None
    if proficiency == "fluent":
        brackets = "[]"
    elif proficiency == "conversational":
        brackets = "()"
    elif proficiency == "learning":
        brackets = "//"
    return ''.join(brackets[0] + new_role_name + brackets[1])


# Adds given language and proficiency to user's roles
@lang.command(name="add", pass_context=True)
async def l_add(ctx, proficiency=None, *, language=None):
    if proficiency is None or proficiency not in proficiencies:
        await ctx.send("Missing proficiency!\n"
                       "Usage: `L!lang [add|remove] [fluent|conversational|learning] <language name/ISO639 code>`\n"
                       "For a list of available languages, try `L!list languages`")
    elif language is None:
        await ctx.send("Missing language!\n"
                       "Usage: `L!lang [add|remove] [fluent|conversational|learning] <language name/ISO639 code>`\n"
                       "For a list of available languages, try `L!list languages`")
    else:
        user = ctx.message.author
        new_role_name = await find_language_role(ctx, proficiency, language)
        if new_role_name is None:
            return
        # Try to find role. If it doesn't exist, create one
        new_role = find(lambda r: r.name == new_role_name,
                        ctx.message.guild.roles)
        if new_role is None:
            new_role = await client.create_role(ctx.message.guild, name=new_role_name)
        if new_role in user.roles:
            await ctx.send("You already have this role!")
        else:
            await user.add_roles(new_role)
            await ctx.send("Added %s to %s's languages" % (new_role_name, user.mention))


# Removes given language and proficiency from user's roles
@lang.command(name="remove", aliases=["rem"], pass_context=True)
async def l_remove(ctx, proficiency=None, *, language=None):
    if proficiency is None or proficiency not in proficiencies:
        await ctx.send("Missing proficiency!\n"
                       "Usage: `L!lang [add|remove] [fluent|conversational|learning] <language name/ISO639 code>`\n"
                       "For a list of available languages, try `L!list languages`")
    elif language is None:
        await ctx.send("Missing language!\n"
                       "Usage: `L!lang [add|remove] [fluent|conversational|learning] <language name/ISO639 code>`\n"
                       "For a list of available languages, try `L!list languages`")
    else:
        user = ctx.message.author
        role_name = await find_language_role(ctx, proficiency, language)
        # Try to find role. If it doesn't exist, say error message.
        role = find(lambda r: r.name == role_name, ctx.message.guild.roles)
        if role is None or role not in user.roles:
            await ctx.send("You don't have this role!")
        else:
            await user.remove_roles(role)
            await ctx.send("Removed %s from %s's languages" % (role_name, user.mention))


# Check a given user's languages
@client.command(aliases=["languages"], pass_context=True)
async def langs(ctx, user=None):
    if user is None:
        user = ctx.message.author
    else:
        user = find(lambda m: m.mentioned_in(
            ctx.message), ctx.message.guild.members)
        if user is None:
            await ctx.send("User not found. Did you @mention them?")
            return
    user_langs = {'Fluent': [], 'Conversational': [], 'Learning': []}
    matcher = re.compile("[\[(/]\w{2,3}[\])/]")
    found = False  # Flag that proves we found at least one role
    # Search through user roles for languages
    for role in user.roles:
        if matcher.fullmatch(role.name):
            found = True
            # Find language
            language = ''
            for entry in languages:
                if entry['iso_639'] == role.name[1:3] or entry['iso_639_2'] == role.name[1:4]:
                    language = entry['name']
                    break
            # Find proficiency
            proficiency = ''
            if role.name[0] == '[':
                proficiency = "Fluent"
            elif role.name[0] == '(':
                proficiency = "Conversational"
            elif role.name[0] == '/':
                proficiency = "Learning"
            user_langs[proficiency].append(language)
    # Print language table
    if not found:
        await ctx.send("{} hasn't added any languages yet!".format(user.name))
        return
    output = ["Listing languages for {}:\n```\n".format(user.name)]
    for s in ['Fluent', 'Conversational', 'Learning']:
        user_langs[s].sort(key=lambda la: la[0])
        for entry in user_langs[s]:
            output.append("{}: {}\n".format(entry, s))
    output.append("```")
    await ctx.send(''.join(output))

############################
#       MOD COMMANDS       #
############################


# Functions for mods to add/remove hosts and update their "office hours"
# frankly I'm not sure how we'll handle any of this yet.
@client.group(hidden=True, pass_context=True)
@commands.has_role("Moderator")
async def host(ctx, *args):
    await ctx.send("`host` not yet implemented :D")


@host.command(name="add")
async def h_add(user):
    pass


@host.command(name="remove", aliases=["rem"])
async def h_remove(user):
    pass


# DM's a warning to the given user
@client.command(hidden=True, pass_context=True)
@commands.has_role("Moderator")
async def warn(ctx, user=None, *, message=None):
    pass


# Updates the nationality and/or language lists so we don't need to restart.
@client.command(hidden=True, pass_context=True)
@commands.has_role("Moderator")
async def update(ctx, ls=None):
    if ls not in ['nationalities', 'languages', 'all']:
        await ctx.send("Please specify: nationalities, languages, or all?")
    else:
        if ls == 'languages' or ls == 'all':
            init_languages()
            await ctx.send("Updated languages.")
        if ls == 'nationalities' or ls == 'all':
            init_nationalities()
            await ctx.send("Updated nationalities.")


client.run(token)
