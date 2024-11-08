import discord;
import json;
import time;
from colors import color_data;

#Json
def get_jsondata_from_file(file):
  with open(file) as json_file:
    data = json.load(json_file)
    return data;

def set_jsondata_to_file(file, data):
  json_string = json.dumps(data)

  # Using a JSON string
  with open(file, 'w') as outfile:
      outfile.write(json_string)

#General
def copy_list(list):
  """
  Copies a list and returns a new list with the same contents
  """
  new_list = [];
  for v in list:
    new_list.append(v); 
  return new_list;

#Discord.Py
def get_embedded_message_data(embed_data, author_data, thumbnail_url, fields, footer_text):
  """
  returns an embedded message given data


  *REQUIRED
  embed_data = ["Title", "URL", "Description", 0xFF5733]

  author_data = ["Name", "URL", "Icon URL"]

  thumbnail_url = https://i.imgur.com/axLm3p6.jpeg;

  fields = [
    ["field title", "field value", inline(boolean)],
    ["field title", "field value", inline(boolean)],
  ]

  footer_text = "some footer text"

  """
  embed=discord.Embed(title=embed_data[0], url=embed_data[1], description=embed_data[2], color=embed_data[3])

  if author_data != None:
    embed.set_author(name=author_data[0], url=author_data[1], icon_url=author_data[2])

  if thumbnail_url != None:
    embed.set_thumbnail(url=thumbnail_url)

  if fields != None:
    for field_data in fields:
      embed.add_field(name=field_data[0],value=field_data[1],inline=field_data[2]);

  default_footer_text = "This bot was created by Mystifine#4924";
  if footer_text != None:
    default_footer_text = footer_text;
  embed.set_footer(text=default_footer_text);

  return embed;
  
def timed_out_msg(interaction):
  embed_data = ["Timed Out", None, f"We couldn't get any input from you! Are you still there {interaction.client.user.name}? Run the command again when you're back.", color_data["red"]];
  thumbnail_url = "https://i.imgur.com/jP3I4Vq.png"; # Timed our URL
  embed_object = get_embedded_message_data(embed_data,None,thumbnail_url,None,None);
  return interaction.edit_original_response(embed=embed_object);

def action_cancelled(interaction):
  embed_data = ["Cancelled", None, f"Action has been cancelled :thumbsup:", color_data["orange"]];
  # thumbnail_url = "https://i.imgur.com/jP3I4Vq.png"; # Timed our URL
  embed_object = get_embedded_message_data(embed_data,None,None,None,None);
  return interaction.edit_original_response(embed=embed_object);

def no_data_found_msg(interaction):
  userName = interaction.client.user.name;
  embed_data = ["No Existing Data Found", None, f"Hey {userName}! We did not find existing data under your Discord UserId. If you wish to start the game use **start** command.", color_data["orange"]];
  embed_object = get_embedded_message_data(embed_data,None,None,None,None);
  return interaction.response.send_message(embed=embed_object);

def add_commas(number):
    return ("{:,}".format(number))

def format_seconds(sec):
  sec = sec % (24 * 3600)
  hour = sec // 3600
  sec %= 3600
  min = sec // 60
  sec %= 60
  return "%02d:%02d:%02d" % (hour, min, sec) 