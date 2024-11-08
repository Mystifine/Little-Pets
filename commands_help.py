import settings;

help_data = {
  "pet" : {
    "desc" : "Displays pet related bot commands",
    "commands" : {
      "start" : [
        "starts your pet taming adventure!",
        "/start",
      ],
      'restart' : [
        "restarts your progress of taming pets.",
        "/restart",
      ],
      'active' : [
        'displays information on your current active pet',
        '/active',
      ],
      'inspect' : [
        'displays information on a pet provided the id',
        '/inspect 5 or /inspect 0 etc',
      ],
      'profile' : [
        'displays the profile of a mentioned member for the game',
        '/profile @mention'
      ],
      'coins' : [
        'displays the amount of coins your pets have generated',
        "/coins",
      ],
      'collect' : [
        'collects the amount of coins your pets have generated',
        "/collect",
      ],
      'pet' : [
        'pet your active pet for some experience!',
        '/pet',
      ],
      'list' : [
        'lists all your pets/tames provided the page',
        '/list 1'
      ],
      'rates' : [
        'lists tame rates',
        '/rates'
      ],
      'info' : [
        'displays information on a pet',
        '/info pet_name'
      ],
      'switch' : [
        'switches the active pet provided the pet id',
        '/switch 5',
      ]
    }
  },

  "general" : {
    "desc" : "Displays some general bot commands",
    "commands" : {
      "invite" : [
        "Generates an invite link that can be used to invite the bot to your discord server!",
        "/invite",
      ],
      "ping" : [
        "Display's the bot latency with the server",
        "/ping",
      ],
      "serverinfo" : [
        "Display's some details about the server",
        "/serverinfo",
      ],
      "avatar" : [
        f"Display the avatar of mentioned user",
        "/avatar @user",
      ],
      "member" : [
        f"Display information mentioned user in one command",
        "/member @user",
      ],
      "uptime" : [
        "Shows how long the bot has been online for",
        "/uptime",
      ],
      "credit" : [
        "Displays credits and contributions to the bot development",
        "/credit",
      ]
    }
  },
  "fun" : {
    "desc" : "Some casual fun and entertaining commands!",
    "commands" : {
      "animal" : [
        "Generates a random image of a animal or animal specified",
        "/animal or /animal cat or /animal red panda"
      ],
      "flip" : [
        "Flips a coin",
        "/flip"
      ],
      "dice" : [
        "Rolls a 6 sided dice",
        "/dice"
      ],
      "animu" : [
        "Generates a gif or image of an anime action",
        "/animu pat or /animu hug"
      ],
      "joke" : [
        "Generates a random joke",
        "/joke"
      ],
      "chance" : [
        "Rolls a chance of an event occuring",
        "/chance event"
      ]
    }, 
  },
}
