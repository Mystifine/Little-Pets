import discord;
from discord import app_commands
from discord.ext import commands

import firebase;
import settings
import asyncio;
import time;
import requests;
import random;
import os

from commands_help import help_data;
from emoji import emoji_data
from colors import color_data;
from monsterdata import monster_data, get_monster_from_name, get_monster_gender, determine_shiny, calcuate_max_exp_from_level;
from util import format_seconds, get_embedded_message_data, timed_out_msg, action_cancelled, get_jsondata_from_file, set_jsondata_to_file, no_data_found_msg, add_commas

bot_start_time = time.perf_counter();
# the @app_commands.guilds and @app_commands.default_permissions decorators (also including checks) can be used above the class.
# these will apply to ALL subcommands, subcommands cannot have invidual perms!

def get_default_playerdata():
  template = {
    "Gold" : 100,
    "Inventory" : {},
    "Active Pet" : {},
    "Pets" : [],

    'Last Pet' : 0,
    'Last Tame' : 0,
  }
  return template;

def get_default_monsterdata(userid, monster):
  monster_data = {
    "id" : monster,
    "level" : 1,
    "exp" : 0,
    "max exp" : 100,

    "gender" : get_monster_gender(monster),
    "shiny" : determine_shiny(userid),
    "shadow" : False,
    'last collected' : time.time(),
  }
  return monster_data;

def get_pet_display_embed_data(name, active_pet_data):
  display_message = ""

  title_desc = f"{name}'s {active_pet_data['id']} Stats"

  display_message += f"""
  {emoji_data["Point"]} **ID**: {active_pet_data['id']}
  {emoji_data["Point"]} **Gender**: {active_pet_data['gender']} {emoji_data[active_pet_data['gender']]}
  {emoji_data["Point"]} **Shiny**: {active_pet_data['shiny']}
  {emoji_data["Point"]} **Shadow**: {active_pet_data['shadow']}
  {emoji_data["Point"]} **Coins Per Hour**: {monster_data[active_pet_data['id']]['coins per hour'] * active_pet_data['level']} {emoji_data['Coin']}
  {emoji_data["Point"]} **Description:** {monster_data[active_pet_data['id']]['description']}
  """

  fields = [];
  # Stats
  exp_percent = active_pet_data["exp"] / active_pet_data["max exp"];
  exp_emoji_display = settings.EXPERIENCE_EMOJI_DISPLAY_COUNT;
  exp_left = round(exp_percent * 10,0);
  monster_stats = f"""
  {emoji_data["Point"]} **Level**: {active_pet_data["level"]}
  """

  monster_stats += f'{emoji_data["Point"]} **Experience**: {active_pet_data["exp"]}/{active_pet_data["max exp"]}\n'
  for i in range(exp_emoji_display):
    if i < exp_left:
      monster_stats += emoji_data["Exp"] 
    else:
      monster_stats += emoji_data["Empty Exp"]
  fields.append(['Pet Stats', monster_stats, True]);

  embed_data = [title_desc, None, display_message, color_data['purple']]
  author_data = [active_pet_data['id'], None, monster_data[active_pet_data["id"]]["image"]]
  display_embed_data = get_embedded_message_data(embed_data,author_data,monster_data[active_pet_data["id"]]["image"],fields,None);
  return display_embed_data;

def give_exp(pet_data, amount):
  pet_data['exp'] += amount;
  while pet_data['exp'] >= pet_data['max exp']:
    pet_data['exp'] -= pet_data['max exp'];
    pet_data['level'] += 1;
    pet_data['max exp'] = calcuate_max_exp_from_level(pet_data['level']);

SECONDS_PER_HOUR = 3600

def get_generated_coins_from_pet(pet_data):
  now = time.time();
  coin_value = round(((now - pet_data['last collected']) / SECONDS_PER_HOUR) - 0.5) * monster_data[pet_data['id']]['coins per hour'] * pet_data['level'];
  return coin_value;

@app_commands.guild_only()
class pet(app_commands.Group):
   # BOT COMMANDS
  @app_commands.command(name='start',description="tame your first pet!")
  async def start(self, interaction:discord.Interaction):
    bot = interaction.client;
    user = interaction.user;

    userid = user.id;
    username = user.name;

    # Check if the player data exists:
    playerdata = firebase.get_data(f"{userid}/pets");
    if playerdata != None:
      # playerdata exists.
      embed_data = ["Existing Data Found", None, f"Hey {username}! We found existing data under your Discord UserId. If you wish to reset your data try the **restart** command!", color_data["orange"]];
      embed_object = get_embedded_message_data(embed_data,None,None,None,None);
      await interaction.response.send_message(embed=embed_object);
    else:
      # New player:
      embed_data = ["Welcome", None, f"Hey {username}! Looks like you're new around here. To start, let's choose a starter monster for you so you can start playing. There are {len(settings.STATER_PETS)} monster buddies you can choose from. **Reply with the name** you want and it'll be yours! You can also say '**cancel**' to cancel this action.", color_data["green"]];
      embeds = [];
      initial_embed_message = get_embedded_message_data(embed_data,None,None,None,None);
      embeds.append(initial_embed_message);
    
      # Display the available starters
      for index in range(len(settings.STATER_PETS)):
        starter = settings.STATER_PETS[index];
        embed_data = [f"Monster #{index+1}", None, monster_data[starter]["description"], color_data["white"]];
        author_data = [starter, None, monster_data[starter]["image"]];
        thumbnail_url = monster_data[starter]["image"];
        fields = [];

        potential_genders_desc = "";
        for gender in monster_data[starter]["gender"]:
          potential_genders_desc = potential_genders_desc + "\n" + f"{emoji_data[gender]} {gender}";
        fields.append(["Potential Gender(s):", potential_genders_desc, False]);
        embed_object = get_embedded_message_data(embed_data,author_data,thumbnail_url,fields,None);
        embeds.append(embed_object);

      await interaction.response.send_message(embeds=embeds);

      # compile the user responses into a list 
      terms = ["cancel"] + settings.STATER_PETS;
      for i in range(len(terms)): 
        terms[i] = terms[i].lower();

      def check(message):
        is_valid = False;
        if message.content.lower() in terms and user == message.author:
          is_valid = True;
        return is_valid
      
      channel = interaction.channel;
      try:
        msg = await bot.wait_for('message', timeout=30.0, check=check)
      except asyncio.TimeoutError:
        await timed_out_msg(interaction);
      else:
        if msg.content.lower() == "cancel":
          await action_cancelled(interaction);
        else:
          selected_monster = msg.content;
          monster, data = get_monster_from_name(selected_monster);
          playerdata = get_default_playerdata();
          new_monster_data = get_default_monsterdata(userid, monster);
          playerdata["Active Pet"] = new_monster_data
          firebase.set_data(f"{userid}/pets", playerdata);

          # Congrats!
          embed_data = ["Congratulations!", None, f"You just made a new monster buddy! You can check on your monster buddy with the /pet active command. For additional commands, use the help command and look under the pet category!", color_data["green"]];
          thumbnail_url = monster_data[monster]["image"];
          author_data = [monster, None, thumbnail_url];
          embed_object = get_embedded_message_data(embed_data,author_data,thumbnail_url,None,None);
          await interaction.followup.send(embed=embed_object);

  @app_commands.command(name='restart',description="restarts your progress, your data will be removed!")
  async def restart(self, interaction:discord.Interaction):
    user = interaction.user;
    bot = interaction.client;

    userid = user.id;
    username = user.name;

    # Check if the player data exists:
    player_data = firebase.get_data(f"{userid}/pets");
    if player_data != None:
      embed_data = ["WARNING", None, "Are you SURE you want to reset your data? If so please reply exactly 'YES' without the quotations.", color_data["orange"]];
      thumbnail_url = "https://i.imgur.com/jP3I4Vq.png"; # warning url
      embed_object = get_embedded_message_data(embed_data,None,thumbnail_url,None,None);
      await interaction.response.send_message(embed=embed_object);

      def check(message):
          is_valid = False;
          if (message.content == "YES" or message.content.lower() == "cancel") and user == message.author:
            is_valid = True;
          return is_valid
        
      try:
        msg = await bot.wait_for('message', timeout=30.0, check=check)
      except asyncio.TimeoutError:
        await timed_out_msg(interaction);
      else:
        if msg.content.lower() == "cancel":
          await action_cancelled(interaction);
        else:
          # This means they said yes
          firebase.delete_data(str(userid));
          embed_data = ["Data Successfully Deleted", None, f"Hello {username}. Your data has been deleted. If you wish to start the game use **start** command.", color_data["green"]];
          embed_object = get_embedded_message_data(embed_data,None,None,None,None);
          await interaction.edit_original_response(embed=embed_object);
    else:
      await no_data_found_msg(interaction)

  @app_commands.command(name='active',description='checks on your active pet')
  async def active(self, interaction:discord.Interaction):
    # retrieve member data:
    user = interaction.user

    display_avatar = user.display_avatar;
    name = user.name;
    userid = user.id;

    # Check if the player data exists:
    playerdata = firebase.get_data(f"{userid}/pets");
    if playerdata != None:
      embed_object = get_pet_display_embed_data(name, playerdata['Active Pet']);
      await interaction.response.send_message(embed=embed_object);
    else:
      await no_data_found_msg(interaction);

  @app_commands.command(name='inspect',description='checks on the provided pet id')
  @app_commands.describe(petid='the pet id you want to inspect. Can be found from /pet list')
  async def inspect(self, interaction:discord.Interaction, petid:int):
    # retrieve member data:
    user = interaction.user

    name = user.name;
    userid = user.id;

    # Check if the player data exists:
    playerdata = firebase.get_data(f"{userid}/pets");
    if playerdata != None:
      if (petid >= 0 and petid <= len(playerdata['Pets']) - 1):
        embed_object = get_pet_display_embed_data(name, playerdata['Pets'][petid]);
        await interaction.response.send_message(embed=embed_object);
      else:
        embed_data = ["No Pet With This Id", None, f"Hey {name}! We did not find a pet with the pet id {petid} in your pet list. Check your pets with /pet list.", color_data["orange"]];
        embed_object = get_embedded_message_data(embed_data,None,None,None,None);
        await interaction.response.send_message(embed=embed_object);
    else:
      await no_data_found_msg(interaction);

  @app_commands.command(name='profile',description="gets information about your profile in game")
  @app_commands.describe(player="The players profile you want to check")
  async def profile(self, interaction:discord.Interaction, player:discord.Member):
    user = player;

    def display_profile(member, member_data):
      # retrieve member data:
      display_avatar = member.display_avatar;
      display_name = member.display_name;
      mention = member.mention;
      name = member.name;
      id = member.id;

      description = f"""
      {emoji_data["Point"]} **Mention**: {mention}
      {emoji_data["Point"]} **ID**: {id}
      """

      title_name = name + " ";
      flags = member.public_flags;

      hypesquad_balance = flags.hypesquad_balance;
      hypesquad_bravery = flags.hypesquad_bravery;
      hypesquad_brilliance = flags.hypesquad_brilliance;
      bot_developer = flags.verified_bot_developer;

      if bot_developer:
        title_name += emoji_data["ActiveBotDeveloper"];

      if hypesquad_bravery:
        title_name += emoji_data["Bravery"];
      elif hypesquad_brilliance:
        title_name += emoji_data["Brilliance"];
      elif hypesquad_balance:
        title_name += emoji_data["Balance"];

      embed_data = [title_name, None, description, color_data["purple"]];
      author_data = [display_name, None, display_avatar];

      fields = [];
      profile_data_text = f"""
      {emoji_data["Point"]} **Coins**: {add_commas(member_data["Gold"])} {emoji_data["Coin"]}
      {emoji_data["Point"]} **Active Pet**: Lv. {member_data["Active Pet"]['level']} {member_data["Active Pet"]['id']} {emoji_data[member_data['Active Pet']['gender']]}
      """
      fields.append([f"Profile Info:", profile_data_text, False]);

      embed_object = get_embedded_message_data(embed_data,author_data,monster_data[member_data["Active Pet"]['id']]["image"],fields,None);
      return interaction.response.send_message(embed=embed_object);

    playerData = firebase.get_data(f"{user.id}/pets");
    if playerData != None:
      # Display player data
      await display_profile(player, playerData);
    else:
      await no_data_found_msg(interaction)

  @app_commands.command(name='coins',description='shows how much coins are available to be collected')
  async def coins(self, interaction:discord.Interaction):
    # retrieve member data:
    user = interaction.user

    name = user.name;
    userid = user.id;

    now = time.time();

    # Check if the player data exists:
    playerdata = firebase.get_data(f"{userid}/pets");
    if playerdata != None:
      total_coins = get_generated_coins_from_pet(playerdata['Active Pet'])
      for pet_data in playerdata['Pets']:
        total_coins += get_generated_coins_from_pet(pet_data)
      # Get the rate limiting headers from the response
      embed_data = ["Coins", None, f'Your pets have collected a total of **{add_commas(total_coins)}**{emoji_data["Coin"]}! Use /pet collect to collect them now.', color_data['green']];
      embed_object = get_embedded_message_data(embed_data,None,None,None,None);
      await interaction.response.send_message(embed=embed_object);
    else:
      await no_data_found_msg(interaction);

  @app_commands.command(name='collect',description='Collects the coins your pets have generated. See how much they generated with /pet coins!')
  async def collect(self, interaction:discord.Interaction):
    # retrieve member data:
    user = interaction.user

    name = user.name;
    userid = user.id;

    now = time.time();

    # Check if the player data exists:
    playerdata = firebase.get_data(f"{userid}/pets");
    if playerdata != None:
      total_coins = get_generated_coins_from_pet(playerdata['Active Pet'])
      if total_coins > 0:
        playerdata['Active Pet']['last collected'] = time.time();
      for i in range(len(playerdata['Pets'])):
        pet_data = playerdata['Pets'][i];
        coin_value = get_generated_coins_from_pet(pet_data);
        total_coins += coin_value
        if coin_value > 0:
          playerdata['Pets'][i]['last collected'] = time.time();
        
      playerdata['Gold'] += total_coins;
      firebase.set_data(f"{userid}/pets", playerdata);
      embed_data = ["Coins Collected", None, f'You have collected **{add_commas(total_coins)}**{emoji_data["Coin"]}!', color_data['green']];
      embed_object = get_embedded_message_data(embed_data,None,None,None,None);
      await interaction.response.send_message(embed=embed_object);
    else:
      await no_data_found_msg(interaction);

  @app_commands.command(name='pet',description='pet your current active pet for some experience')
  async def pet(self, interaction:discord.Interaction):
    # retrieve member data:
    user = interaction.user

    name = user.name;
    userid = user.id;

    now = time.time();

    # Check if the player data exists:
    playerdata = firebase.get_data(f"{userid}/pets");
    if playerdata != None:
      previous_level = playerdata['Active Pet']['level'];
      if (now - playerdata['Last Pet']) >= settings.PET_COOLDOWN:
        give_exp(playerdata['Active Pet'], settings.PET_EXP);
        body_text = f'{name} petted their pet! Their pet {playerdata["Active Pet"]["id"]} liked it and gained **{settings.PET_EXP}** experience.';
        if playerdata['Active Pet']['level'] > previous_level:
          body_text += f" **{name}'s pet leveled up!**";
        playerdata['Last Pet'] = now;
        firebase.set_data(f'{userid}/pets', playerdata);
        embed_data = ["Pet", None, body_text, color_data['green']];
        embed_object = get_embedded_message_data(embed_data,None,None,None,None);
        await interaction.response.send_message(embed=embed_object);
      else:
        embed_data = ["On Cooldown", None, f"You can pet your pet again in {format_seconds(settings.PET_COOLDOWN - (now - playerdata['Last Pet']))}", color_data['orange']];
        embed_object = get_embedded_message_data(embed_data,None,None,None,None);
        await interaction.response.send_message(embed=embed_object);
    else:
      await no_data_found_msg(interaction);

  @app_commands.command(name='tame',description='tame a wild monster!')
  async def tame(self, interaction:discord.Interaction):
    # retrieve member data:
    user = interaction.user

    name = user.name;
    userid = user.id;

    now = time.time();

    # Check if the player data exists:
    playerdata = firebase.get_data(f"{userid}/pets");
    if playerdata != None:
      if (now - playerdata['Last Tame']) >= settings.TAME_COOLDOWN:
        total_weight = 0;
        tame_list = [];
        for monster, monster_info in monster_data.items():
          total_weight += monster_info['occurance weight'];
          tame_list.append([monster, total_weight]);
        random_number = total_weight * random.random();

        # Selecting the random monster:
        tame_monster = "";
        for i in range(len(tame_list)):
          tame_data = tame_list[i];
          monster_id = tame_data[0];
          value = tame_data[1];
          if random_number <= value:
            tame_monster = monster_id;
            break;
        pet_data = get_default_monsterdata(userid,tame_monster);
        body_text = f"""
        {name} Wandered the woods and forests,
        Crossed seven oceans and seas,
        Traveled several deserts...

        and tamed a **{tame_monster}**!

        Here are the {tame_monster}'s stats:
        {emoji_data["Point"]} **ID**: {tame_monster}
        {emoji_data["Point"]} **Gender**: {pet_data['gender']} {emoji_data[pet_data['gender']]}
        {emoji_data["Point"]} **Shiny**: {pet_data['shiny']}
        {emoji_data["Point"]} **Shadow**: {pet_data['shadow']}
        {emoji_data["Point"]} **Coins Per Hour**: {monster_data[pet_data['id']]['coins per hour'] * pet_data['level']} {emoji_data['Coin']}
        """
        playerdata['Pets'].append(pet_data);
        playerdata['Last Tame'] = now;
        firebase.set_data(f"{userid}/pets", playerdata);
        author_data = [name, None, user.avatar]
        embed_data = ["Tame", None, body_text, color_data['purple']];
        embed_object = get_embedded_message_data(embed_data,author_data,None,None,None);
        embed_object.set_image(url=monster_data[tame_monster]['image']);
        await interaction.response.send_message(embed=embed_object);
      else:
        embed_data = ["On Cooldown", None, f"You can tame a wild pet again in {format_seconds(settings.TAME_COOLDOWN - (now - playerdata['Last Tame']))}", color_data['orange']];
        embed_object = get_embedded_message_data(embed_data,None,None,None,None);
        await interaction.response.send_message(embed=embed_object);
    else:
      await no_data_found_msg(interaction);

  @app_commands.command(name='list', description=f'lists a page of your pets. Each page will display upto {settings.PET_PER_PAGE} pets')
  @app_commands.describe(page_number = 'page number you want to display. The starting number is 1')
  async def list(self, interaction:discord.Interaction, page_number:int):
    # retrieve member data:
    user = interaction.user

    name = user.name;
    userid = user.id;

    # Check if the player data exists:
    playerdata = firebase.get_data(f"{userid}/pets");
    if playerdata != None:
      if page_number > 0:
        start_index = (page_number-1) * settings.PET_PER_PAGE;
        end_index = start_index + settings.PET_PER_PAGE;
        foot_note = f"CPH means coins per hour | Page {page_number}";
        body_text = f""

        if len(playerdata['Pets']) >= start_index:
          end_index = end_index if len(playerdata['Pets']) > end_index else len(playerdata['Pets'])
          for i in range(start_index, end_index):
            pet_data = playerdata['Pets'][i];
            body_text += f"\n#{i} {emoji_data[pet_data['gender']]} Lv. **{pet_data['level']} {pet_data['id']}** | **Exp**: {pet_data['exp']}/{calcuate_max_exp_from_level(pet_data['level'])} | {monster_data[pet_data['id']]['coins per hour'] * pet_data['level']} {emoji_data['Coin']} CPH";
        
        author_data = [name, None, user.avatar]
        embed_data = [f"{name}'s Page {page_number} Pet List:", None, body_text, color_data['purple']];
        embed_object = get_embedded_message_data(embed_data,author_data,None,None,foot_note);
        await interaction.response.send_message(embed=embed_object);
      else:
        embed_data = ["Error", None, f"{page_number} is not a valid page number. Please use the starting page 1.", color_data['red']];
        embed_object = get_embedded_message_data(embed_data,None,None,None,None);
        await interaction.response.send_message(embed=embed_object);
    else:
      await no_data_found_msg(interaction);

  @app_commands.command(name='rates',description='monster tame rates')
  async def rates(self, interaction:discord.Interaction):
    # retrieve member data:
    user = interaction.user
    bot = interaction.client;

    name = user.name;
    userid = user.id;

    body_text = f"";
    
    total_weight = 0;
    tame_list = [];
    for monster, monster_info in monster_data.items():
      total_weight += monster_info['occurance weight'];

    for monster, monster_info in monster_data.items():
      rate = round((monster_info['occurance weight'] / total_weight)*100, 3);  
      body_text += f"\n{emoji_data['Point']} {monster} ({rate}%)"
    author_data = [bot.user.name, None, user.avatar]
    embed_data = ["Tame Rates", None, body_text, color_data['purple']];
    embed_object = get_embedded_message_data(embed_data,author_data,None,None,None);
    await interaction.response.send_message(embed=embed_object);

  @app_commands.command(name='info',description='check the information on a specific pet')
  @app_commands.describe(pet_name = 'the pet you want info on')
  async def info(self, interaction:discord.Interaction, pet_name:str):
    monster, monster_info = get_monster_from_name(pet_name);
    if monster != None:
      # retrieve member data:
      user = interaction.user
      name = user.name;

      display_message = ""

      title_desc = f"Information on {monster}"

      display_message += f"""
      {emoji_data["Point"]} **ID**: {monster}
      {emoji_data["Point"]} **Description:** {monster_data[monster]['description']}
      """
      potential_genders_desc = "";
      for gender in monster_data[monster]["gender"]:
        potential_genders_desc = potential_genders_desc + f"{emoji_data[gender]} {gender}, ";
      display_message += f"{emoji_data['Point']} **Potential Gender(s)**: " + potential_genders_desc;
      display_message += f"\n{emoji_data['Point']} **Coins Per Hour**: {monster_data[monster]['coins per hour']} {emoji_data['Coin']}"

      embed_data = [title_desc, None, display_message, color_data['purple']]
      author_data = [monster, None, monster_data[monster]["image"]]
      display_embed_data = get_embedded_message_data(embed_data,author_data,monster_data[monster]["image"],None,None);
      await interaction.response.send_message(embed=display_embed_data);
    else:
      embed_data = ["Doesn't Exist", None, f"Could not find **{pet_name}'s data**. Are you sure you spelt it right?", color_data['orange']];
      embed_object = get_embedded_message_data(embed_data,None,None,None,None);
      await interaction.response.send_message(embed=embed_object);

  @app_commands.command(name='switch', description='switches your active pet with one of your other tames provided the pet id')
  @app_commands.describe(petid='the pet id you want to switch with. Can be found from /pet list')
  async def inspect(self, interaction:discord.Interaction, petid:int):
    # retrieve member data:
    user = interaction.user

    name = user.name;
    userid = user.id;

    # Check if the player data exists:
    playerdata = firebase.get_data(f"{userid}/pets");
    if playerdata != None:
      if (petid >= 0 and petid <= len(playerdata['Pets']) - 1):
        pet_data = playerdata['Pets'][petid];
        active_pet_data = playerdata['Active Pet'];
        
        # Switch the data
        playerdata['Pets'][petid] = active_pet_data;
        playerdata['Active Pet'] = pet_data;

        firebase.set_data(f"{userid}/pets", playerdata);

        embed_data = ["Switched", None, f"You've switched your active pet {emoji_data[playerdata['Pets'][petid]['gender']]} **Lv. {playerdata['Pets'][petid]['level']} {playerdata['Pets'][petid]['id']}** with {emoji_data[playerdata['Active Pet']['gender']]} **Lv. {playerdata['Active Pet']['level']} {playerdata['Active Pet']['id']}**", color_data["orange"]];
        embed_object = get_embedded_message_data(embed_data,None,None,None,None);

        await interaction.response.send_message(embed=embed_object);
      else:
        embed_data = ["No Pet With This Id", None, f"Hey {name}! We did not find a pet with the pet id {petid} in your pet list. Check your pets with /pet list.", color_data["green"]];
        embed_object = get_embedded_message_data(embed_data,None,None,None,None);
        await interaction.response.send_message(embed=embed_object);
    else:
      await no_data_found_msg(interaction);

animal_options = ["bird","cat","dog","fox","kangaroo","koala","panda","racoon","red_panda"];
async def animal_autocomplete(interaction: discord.Interaction, current: str):
  shortened_animal_reactions = animal_options[:25];
  return [
      app_commands.Choice(name=animal, value=animal)
      for animal in shortened_animal_reactions if current.lower() in animal.lower()
  ]

animu_reactions = requests.get("https://api.otakugifs.xyz/gif/allreactions").json()['reactions']
async def reaction_autocomplete(interaction: discord.Interaction, current: str):
  shortened_animu_reactions = animu_reactions[:25];
  return [
      app_commands.Choice(name=reaction, value=reaction)
      for reaction in shortened_animu_reactions if current.lower() in reaction.lower()
  ]

@app_commands.guild_only()
class fun(app_commands.Group):
  @app_commands.command(name='animal',description="generates a random animal image")
  @app_commands.describe(animal = 'the animal you want an image of. Available Options: "bird","cat","dog","fox","kangaroo","koala","panda","racoon","red panda"')
  @app_commands.autocomplete(animal = animal_autocomplete)
  async def animal(self, interaction: discord.Interaction, animal: str):
    start_time = time.perf_counter();

    body_text = None;
    if not animal in animal_options:
      animal = random.choice(animal_options)
      body_text = f"I couldn't find what you were looking for. Here's a {animal} image instead!"

    # Make a GET request to the API endpoint to get a random animal image
    response = requests.get("https://some-random-api.ml/animal/" + animal)
    # Get the URL of the cat image from the response
    image_url = response.json()["image"];
    random_fact = response.json()["fact"];

    if body_text != None:
      body_text += f"""
      **Did you know?**
      {random_fact}
      """
    else:
      body_text = f"""
      **Did you know?**
      {random_fact}
      """
  
    bot_stats = get_jsondata_from_file("bot-stats.json");
    if "Generated Animal Images" in bot_stats:
      bot_stats["Generated Animal Images"] += 1;
    else:
      bot_stats["Generated Animal Images"] = 1;
    set_jsondata_to_file('bot-stats.json', bot_stats);

    elapsed_time = round(time.perf_counter() - start_time,3);
    embed_data = [f"Random {animal} image", None, body_text, color_data["purple"]];
    footer_text = f"I've generated a total of {bot_stats['Generated Animal Images']} animal images! | Image was generated in {elapsed_time} second(s)."
    embed_object = get_embedded_message_data(embed_data,None,None,None,footer_text);
    embed_object.set_image(url=image_url);
    await interaction.response.send_message(embed=embed_object);

  @app_commands.command(name='animu',description="generates an animu action")
  @app_commands.describe(action = 'the anime action you want.')
  @app_commands.autocomplete(action=reaction_autocomplete)
  async def animu(self, interaction: discord.Interaction, action: str):
    start_time = time.perf_counter();
    animu_endpoint = "https://api.otakugifs.xyz/gif?reaction="
    
    body_text = None;
    if not action in animu_reactions:
      action = random.choice(animu_reactions);
      body_text = f"I couldn't find what you were looking for. Here's a {action} reaction instead!"

    # Make a GET request to the API endpoint to get a random animu action
    response = requests.get(animu_endpoint + action)
    json_data = response.json();
    # Get the URL of the cat image from the response
    link = json_data["url"];
  
    bot_stats = get_jsondata_from_file("bot-stats.json");
    if "Generated Animu Actions" in bot_stats:
      bot_stats["Generated Animu Actions"] += 1;
    else:
      bot_stats["Generated Animu Actions"] = 1;
    set_jsondata_to_file('bot-stats.json', bot_stats);

    elapsed_time = round(time.perf_counter() - start_time,3);
    embed_data = [f"{action}", None, body_text, color_data["purple"]];
    footer_text = f"I've generated a total of {bot_stats['Generated Animu Actions']} animu actions! | action was generated in {elapsed_time} second(s)."
    embed_object = get_embedded_message_data(embed_data,None,None,None,footer_text);
    embed_object.set_image(url=link);
    await interaction.response.send_message(embed=embed_object);

  @app_commands.command(name='joke',description="generates a random joke")
  async def joke(self, interaction: discord.Interaction):
    start_time = time.perf_counter();
    
    # Make a GET request to the API endpoint to get a random cat image
    response = requests.get("https://some-random-api.ml/others/joke")
    # Get the URL of the cat image from the response
    joke = response.json()["joke"];
  
    bot_stats = get_jsondata_from_file("bot-stats.json");
    if "Generated Jokes" in bot_stats:
      bot_stats["Generated Jokes"] += 1;
    else:
      bot_stats["Generated Jokes"] = 1;
    set_jsondata_to_file('bot-stats.json', bot_stats);

    elapsed_time = round(time.perf_counter() - start_time,3);
    embed_data = [f"Random Joke", None, joke, color_data["purple"]];
    footer_text = f"I've generated a total of {bot_stats['Generated Jokes']} jokes! | joke was generated in {elapsed_time} second(s)."
    embed_object = get_embedded_message_data(embed_data,None,None,None,footer_text);
    await interaction.response.send_message(embed=embed_object);

  @app_commands.command(name='flip',description="flips a coin")
  async def flip(self, interaction: discord.Interaction):
    value = "Heads" if random.randint(1,2) == 1 else "Tails";
    embed_data = ["Flipping A Coin", None, f'I got {value}!', color_data["black"]];

    bot_stats = get_jsondata_from_file("bot-stats.json");
    if "Coins Flipped" in bot_stats:
      bot_stats["Coins Flipped"] += 1;
    else:
      bot_stats["Coins Flipped"] = 1;
    set_jsondata_to_file('bot-stats.json', bot_stats);  
    footer_text = f"We've flipped a total of {bot_stats['Coins Flipped']} coins!!"
    embed_object = get_embedded_message_data(embed_data,None,None,None,footer_text);
    await interaction.response.send_message(embed=embed_object);

  @app_commands.command(name='dice',description="rolls a 6 sided dice")
  async def dice(self, interaction: discord.Interaction):
    value = random.randint(1,6);
    embed_data = ["Rolling a dice", None, f'I rolled a {value}!', color_data["black"]];

    bot_stats = get_jsondata_from_file("bot-stats.json");
    if "Dices Rolled" in bot_stats:
      bot_stats["Dices Rolled"] += 1;
    else:
      bot_stats["Dices Rolled"] = 1;
    set_jsondata_to_file('bot-stats.json', bot_stats);  
    footer_text = f"We've rolled a total of {bot_stats['Dices Rolled']} dices!"
    embed_object = get_embedded_message_data(embed_data,None,None,None,footer_text);
    await interaction.response.send_message(embed=embed_object);

  @app_commands.command(name="chance",description="Randomly generates a number from 1-100 representing a percent of the chance of something occuring.")
  @app_commands.describe(event = "The event that you want the chance of occuring")
  async def chance(self, interaction: discord.Interaction, event: str):
    odds = random.randint(1,100);
    embed_data = ["Seeing into the future...", None, f'There is a **{odds}**% chance of {event}!', color_data["black"]];

    bot_stats = get_jsondata_from_file("bot-stats.json");
    if "Futures Seen" in bot_stats:
      bot_stats["Futures Seen"] += 1;
    else:
      bot_stats["Futures Seen"] = 1;
    set_jsondata_to_file('bot-stats.json', bot_stats);  
    footer_text = f"I've seen {bot_stats['Futures Seen']} future events!"
    embed_object = get_embedded_message_data(embed_data,None,None,None,footer_text);
    await interaction.response.send_message(embed=embed_object);

@app_commands.guild_only()
class help(app_commands.Group):
  # BOT COMMANDS
  @app_commands.command(name='help',description="a list of helpful commands")
  @app_commands.describe(category="the category you want help in. You can use 'help' to see a list of categories.")
  async def help(self, interaction:discord.Interaction,category:str):
    category = category.strip().lower();
    if not category in help_data:
      desc = f"""
      **{emoji_data["Online"]} Welcome to the help menu!**
      You can use the general prefix '/' or mention the bot to run commands.
      If any command breaks please contact Mystifine#4924 about it.
      To view commands specific to a category use `/help category_name`.
      **Example:** `/help game`.
      I'll go ahead and list the available categories below!
      One more thing, commands are not case-sensitive! {emoji_data["Ghost"]}
      """
      embed_data = ["Help Menu", None, desc, color_data["white"]];
      author_data = [f"{interaction.client.user.name}", None, interaction.client.user.avatar];
      
      fields = [];
      for key, value in help_data.items():
        fields.append([f"{emoji_data['Point']} {key.upper()}", value["desc"], False]);

      embed_object = get_embedded_message_data(embed_data,author_data,monster_data["Ghost"]["image"],fields,None);
      await interaction.response.send_message(embed=embed_object);
    else:
      desc = f"""
      **{emoji_data["Online"]} Commands:**
      This is what we found in {category} command category!
      """
      embed_data = ["Commands", None, desc, color_data["white"]];
      author_data = [f"{interaction.client.user.name}", None, interaction.client.user.avatar];
      
      fields = [];
      for cmd, data in help_data[category]["commands"].items():
        msg = f"""
        **Description**: {data[0]}
        **Example:** `{data[1]}` 
        """
        fields.append([f"{emoji_data['Point']} {cmd}", msg, False]);

      embed_object = get_embedded_message_data(embed_data,author_data,monster_data["Ghost"]["image"],fields,None);
      await interaction.response.send_message(embed=embed_object);

@app_commands.guild_only()
class general(app_commands.Group):
  @app_commands.command(name='ping',description="gets bot latency")
  async def ping(self, interaction: discord.Interaction):
    # Get the rate limiting headers from the response
    value = round(interaction.client.latency * 1000);
    color = color_data["green"] if value < 150 else color_data["orange"] if value < 500 else color_data["red"];
    embed_data = ["Pong", None, f'{value}ms', color];
    embed_object = get_embedded_message_data(embed_data,None,None,None,None);
    await interaction.response.send_message(embed=embed_object);

  @app_commands.command(name='serverinfo',description="gets information about the server")
  async def serverinfo(self, interaction: discord.Interaction):
    guild = interaction.guild;

    guild_name = guild.name;
    guild_icon = guild.icon;
    guild_id = guild.id;
    guild_description = guild.description;
    guild_bitratelimit = guild.bitrate_limit;
    guild_created_at = guild.created_at.strftime("%A, %B %d %Y @ %H:%M:%S %p");
    guild_emoji_limit = guild.emoji_limit;
    guild_max_members = guild.max_members;
    guild_owner = guild.owner;
    guild_owner_id = guild.owner_id;
    guild_members = guild.members;
    guild_shardid = guild.shard_id;
    guild_sticker_limit = guild.sticker_limit;
    guild_voice_channels = guild.voice_channels;
    guild_text_channels = guild.text_channels;
    guild_file_size_limit = guild.filesize_limit;
    guild_premium_subscriber_count = guild.premium_subscription_count;
    guild_premium_tier = guild.premium_tier;
    guild_premium_subscriber_role = guild.premium_subscriber_role;
    guild_mfa_level = guild.mfa_level;
    guild_nsfw_level = guild.nsfw_level;
    guild_vanity_url = guild.vanity_url;

    bots = 0;
    for member in guild_members:
      if member.bot:
        bots += 1;

    server_desc = f"""
    {emoji_data["Ghost"]} **Server Id**: {guild_id}
    {emoji_data["Ghost"]} **Server Description**: {guild_description}
    {emoji_data["Ghost"]} **Creation Date**: {guild_created_at}
    {emoji_data["Ghost"]} **Owner**: {guild_owner}
    {emoji_data["Ghost"]} **Owner Id**: {guild_owner_id}
    {emoji_data["Ghost"]} **Shard Id**: {guild_shardid}
    {emoji_data["Ghost"]} **Multi-Factor Authentication Level**: {guild_mfa_level}
    {emoji_data["Ghost"]} **NSFW Level**: {guild_nsfw_level}
    {emoji_data["Ghost"]} **Vanity URL**: {guild_vanity_url}

    """
    embed_data = ["Server Info", None, server_desc, color_data["white"]];
    author_data = [f"Server Name: {guild_name}", None, guild_icon];
    
    fields = [];
    members_desc = f"""
    {emoji_data["Ghost"]} **Max Members**: {guild_max_members}
    {emoji_data["Ghost"]} **Total Members**: {len(guild_members)}
    {emoji_data["Ghost"]} **Humans**: {len(guild_members) - bots}
    {emoji_data["Ghost"]} **Bots**: {bots}
    """
    fields.append([f"Members Info:", members_desc, False]);
    
    channels_desc = f"""
    {emoji_data["Ghost"]} **Text Channels**: {len(guild_text_channels)}
    {emoji_data["Ghost"]} **Voice Channels**: {len(guild_voice_channels)}
    """
    fields.append([f"Server Channels:", channels_desc, False]);

    server_limit_desc = f"""
    {emoji_data["Ghost"]} **Bitrate Limit**: {str(guild_bitratelimit) + " bit(s)"}
    {emoji_data["Ghost"]} **Filesize Limit**: {str(guild_file_size_limit) + " byte(s)"}
    {emoji_data["Ghost"]} **Emoji Limit**: {guild_emoji_limit}
    {emoji_data["Ghost"]} **Sticker Limit**: {guild_sticker_limit}
    """
    fields.append([f"Server Limits:", server_limit_desc, False]);

    nitro_desc = f"""
    {emoji_data["Nitro"]} **Nitro Boosters**: {guild_premium_subscriber_count}
    {emoji_data["Nitro"]} **Nitro Booster Role**: {guild_premium_subscriber_role}
    {emoji_data["Nitro"]} **Nitro Server Tier**: {"Level: " + str(guild_premium_tier)}
    """
    fields.append([f"Nitro Info:", nitro_desc, True]);

    embed_object = get_embedded_message_data(embed_data,author_data,monster_data["Ghost"]["image"],fields,None);
    await interaction.response.send_message(embed=embed_object);

  @app_commands.command(name='member',description="gets information about the member")
  @app_commands.describe(member="the member you want information on")
  async def member(self, interaction:discord.Interaction, member:discord.Member):
    # retrieve member data:
    display_avatar = member.display_avatar;
    is_bot = member.bot;
    activities = member.activities
    display_name = member.display_name;
    created_at = member.created_at.strftime("%A, %B %d %Y @ %H:%M:%S %p");
    joined_at = member.joined_at.strftime("%A, %B %d %Y @ %H:%M:%S %p");
    top_role = member.top_role;
    premium_since = member.premium_since;
    name = member.name;
    desktop_status = member.desktop_status;
    web_status = member.web_status;
    mobile_status = member.mobile_status;
    color = member.color;
    id = member.id;
    mention = member.mention;

    description = f"""
    {emoji_data["Ghost"]} **Mention**: {mention}
    {emoji_data["Ghost"]} **ID**: {id}
    {emoji_data["Ghost"]} **Created At**: {created_at}
    {emoji_data["Ghost"]} **Is Bot**: {is_bot}

    **Current Acitivty**: {activities}
    """

    title_name = name + " ";
    flags = member.public_flags;

    hypesquad_balance = flags.hypesquad_balance;
    hypesquad_bravery = flags.hypesquad_bravery;
    hypesquad_brilliance = flags.hypesquad_brilliance;
    bot_developer = flags.verified_bot_developer;

    if bot_developer:
      title_name += emoji_data["ActiveBotDeveloper"];

    if hypesquad_bravery:
      title_name += emoji_data["Bravery"];
    elif hypesquad_brilliance:
      title_name += emoji_data["Brilliance"];
    elif hypesquad_balance:
      title_name += emoji_data["Balance"];

    embed_data = [title_name, None, description, color];
    author_data = [display_name, None, display_avatar];
    
    fields = [];
    server_info = f"""
    {emoji_data["Ghost"]} **Joined At**: {joined_at}
    {emoji_data["Ghost"]} **Top Role**: {top_role}
    {emoji_data["Ghost"]} **Premium Since**: {premium_since}
    """
    fields.append([f"Server Info:", server_info, False]);
    local_emoji_data = {
      "dnd" : "DND",
      "online" : "Online",
      "idle" : "Idle",
      "offline" : "Offline",
    }
    
    user_status = f"""
    {emoji_data[local_emoji_data[str(desktop_status)]]} **Desktop Status:** {desktop_status}
    {emoji_data[local_emoji_data[str(web_status)]]} **Website Status:** {web_status}
    {emoji_data[local_emoji_data[str(mobile_status)]]} **Mobile Status:** {mobile_status}
    """
    fields.append([f"User Status:", user_status, False]);

    embed_object = get_embedded_message_data(embed_data,author_data,monster_data["Flowel"]["image"],fields,None);
    await interaction.response.send_message(embed=embed_object);

  @app_commands.command(name='avatar',description="gets a avatar of the mentioned users")
  @app_commands.describe(member="the member you want avatar displayed")
  async def avatar(self, interaction:discord.Interaction, member:discord.Member):
    avatar_icon = member.avatar;
    embed_data = [f"{member.name}'s Avatar", None, None, color_data["black"]];
    author_data = [member.name, None, None];
    thumbnail_url = avatar_icon; 
    embed_object = get_embedded_message_data(embed_data,author_data,None,None,None);
    embed_object.set_image(url=thumbnail_url)
    await interaction.response.send_message(embed=embed_object);

  @app_commands.command(name='credit',description="credits")
  async def credit(self, interaction:discord.Interaction):
    credit_text = "Appreciation of contributors:";
    for contributor, roles in settings.CREDITS.items():
      credit_text += f"\n{emoji_data['Ghost']} **{contributor}**: ";
      for role in roles:
        credit_text += f"{role}" + ", ";

    embed_data = ["Credits", None, credit_text, color_data["purple"]];
    thumbnail_url = monster_data["Jellybean"]["image"]; 
    embed_object = get_embedded_message_data(embed_data,None,thumbnail_url,None,None);
    await interaction.response.send_message(embed=embed_object);

  @app_commands.command(name='uptime',description="shows how long the bot has been active for")
  async def uptime(self, interaction:discord.Interaction):
    elapsed_time = time.perf_counter() - bot_start_time;
    time_format = time.strftime("%H:%M:%S", time.gmtime(elapsed_time))
    embed_data = ["Uptime", None, f"**Elapsed**: {time_format}", color_data["green"]];
    thumbnail_url = monster_data["Jellybean"]["image"]; 
    embed_object = get_embedded_message_data(embed_data,None,thumbnail_url,None,None);
    await interaction.response.send_message(embed=embed_object);

  @app_commands.command(name='invite',description="gets an invite to add the bot to your server!")
  async def invite(self, interaction:discord.Interaction):
    value = os.getenv("BOT_INVITE_URL");
    embed_data = ["Invite", value, "Use the hyper link to invite me to your discord server!", color_data["green"]];
    embed_object = get_embedded_message_data(embed_data,None,None,None,None);
    await interaction.response.send_message(embed=embed_object);

# unlike commands.GroupCog, you need to add this class to your tree yourself.
async def setup(client):
  client.tree.add_command(fun());
  client.tree.add_command(help());
  client.tree.add_command(general());
  client.tree.add_command(pet());
  try:
    synced = await client.tree.sync();
    print(f"Synced {len(synced)} group command(s)");
  except Exception as e:
    print(e);

