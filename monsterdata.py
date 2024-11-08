import random;
import settings;

# Monster Images Must be 100x100

monster_data = {
  "Ghost" : {
    "image" : "https://i.imgur.com/AZHWXd6.png",
    "description" : "ghost likes to scare people when they aren't paying attention.",

    "gender" : ["Male", "Female", "Genderless"],
    "coins per hour": 5,
    "occurance weight": 10,
  },

  "Flowel" : {
    "image" : "https://i.imgur.com/weNK7d5.png",
    "description" : "flowel, an owl type monster that likes to sleep in the day instead of the night.",

    "gender" : ["Male", "Female"],
    "coins per hour": 5,
    "occurance weight": 10,
  },

  "Jellybean" : {
    "image" : "https://i.imgur.com/lSa8tCn.png",
    "description" : "it's origins are unknown but these friendly little monsters do no harm.",

    "gender" : ["Male", "Female"],
    "coins per hour": 5,
    "occurance weight": 10,
  },

  "Slime" : {
    "image" : "https://i.imgur.com/xkz5pvl.png",
    "description" : "a common monster that lurks in the green lands.",
    "gender" : ["Genderless"],
    "coins per hour": 7,
    "occurance weight": 8,
  },

  "Meowy" : {
    "image" : "https://i.imgur.com/uh8NHZJ.png",
    "description" : "lazy as it is, it's nice to cuddle.",
    "gender" : ["Female", "Male"],
    "coins per hour" : 7,
    "occurance weight" : 8,
  },

  "Flor" : {
    "image" : "https://i.imgur.com/dfVFeoh.png",
    "description" : "a gentle creature that lives in the magical forest",
    "gender" : ["Female","Male"],
    "coins per hour" : 7,
    "occurance weight" : 8,
  },

  "Felicia" : {
    "image" : "https://i.imgur.com/b9XBUFk.png",
    "description" : "our dream.",
    "gender" : ["Female"],
    "coins per hour" : 30,
    "occurance weight" : 0.1,
  },

  "Mini Kanna" : {
    "image" : "https://i.imgur.com/9WWtlaO.png",
    "description" : "mini kanna!",
    "gender" : ["Female"],
    "coins per hour" : 30,
    "occurance weight" : 0.1,
  }
}

def get_monster_from_name(monster_name:str):
  for monster, data in monster_data.items():
    lowered = monster.lower();
    if lowered == monster_name.lower():
      return monster, data;

  return None, None;

def get_monster_gender(monster_name):
  random_gender = monster_data[monster_name]["gender"][random.randint(0,len(monster_data[monster_name]["gender"])-1)];
  return random_gender;

def determine_shiny(user):
  rand_number = random.random();
  is_shiny = False;
  if rand_number <= (settings.SHINY_CHANCE/100):
    is_shiny = True;
  return is_shiny;

def calcuate_max_exp_from_level(level):
  return 100 * level;
