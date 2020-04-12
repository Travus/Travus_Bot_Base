<p align="center"><img src="https://i.imgur.com/EekoTeO.png" alt="Travus Bot Base" width="450"/><br/><br/></p>

This is the Travus Bot Base, a basic starting point for Discord bots using [Discord.py](https://github.com/Rapptz/discord.py). The bot comes with all the basic functionality you need and is intended to be further extended with functionality specific to your needs. The basic included functionality is managing prefix, hiding and disabling commands, and easily generating rich help entries for commands and other essential functionality. The main draw of the Travus Bot Base framework is its easy extendability. The bot can technically work in multiple servers at once, but this is not intended as all settings and modules will be global across all servers. To run the bot with independent settings in different servers, run multiple separate instances of it.

The intended use-case for this bot base is to be used by small to medium servers as a starting-point to build a bot for their server from. All essential functions such as changing prefix and such are already set up, and additional functionality can be added via 'modules' which can be loaded and unloaded on-the-fly without restarting the bot or disrupting other modules that might be loaded. This bot is not very feature backed, as it is intended to be a starting point to make you own custom bots from, as such it does not come with any bells and whistles outside of generic commands for maintaining bot-wide functionality such as prefixes, command help, turning commands on and off, adding and removing additional functions, and so forth.

---

### Table of Contents

- [Installation](#installation)
- [Included Commands](https://github.com/Travus/Travus_Bot_Base/wiki/Commands)
- [Making Your Own Modules](https://github.com/Travus/Travus_Bot_Base/wiki/Module_Creation)
- [Documentation](https://github.com/Travus/Travus_Bot_Base/wiki/Documentation)
- [Additional Customization](https://github.com/Travus/Travus_Bot_Base/wiki/Customization)
- [Contact & Credits](#contact--credits)

---
### Installation
> **_NOTE:_**  This bot runs on, and requires [Python](https://www.python.org/) 3.6 or newer.

**1: Create a Discord Application with Bot**  
First, you need to set up a Discord Bot account. In order to do this, you need to go to [Discord's Developer Portal](https://discordapp.com/developers/applications/). From here, press the *New Application* button in the top right, and give it a name. Next, on the panel to the left, navigate to the *Bot* tab. Here, click the *Add Bot* button on the right, and confirm.

**2: Set Bot Name, Image & Get the Token**  
Here you can choose the bot's name, and profile image. You can also choose whether only you, or everyone with the invite link - which we will come back to - can invite the bot. Lastly, you can click the *Click to Reveal Token* button, to see your bot token. We will use this token later, so make a note of it. Also make extra sure this token does not get into the wrong hands, as everyone with the token will be able to run code using your bot.

**3: Invite the Bot**  
Lastly, go back to the *General Information* page via the panel on the left. Take the 18 digit number listed as *CLIENT ID* from here, and insert it into the *Client ID* field on [this website](https://discordapi.com/permissions.html). Check the permissions you want to give your bot, and click the link it generates at the bottom of the page. Using this you can invite your bot to your server.

**4: (Optional) Set Up a Virtual Environment**  
It is recommended to run your bot in it's own virtual environment. You should really run most of your projects in separate environments. A virtual environment acts as it's own installation of python, separate from any other virtual environments or installations of Python. This way you can have different projects using different versions of dependencies. If you run all your projects in the same environment you will sooner or later run into issues where different libraries require different versions of the same packages from one another. One way of dealing with this is by using [venv](https://docs.python.org/3/library/venv.html), though alternatives such as pipenv do exist. This step is technically optional, though heavily recommended.

**5: Installing Discord.py**  
Once you have created and activated a virtual environment (Or are following along without one.) we need to install [Discord.py](https://github.com/Rapptz/discord.py) by [Rapptz](https://github.com/Rapptz). This can be done with one of the the following command-line commands:  
Without voice support: `python -m pip install -U discord.py`  
With voice support: `python -m pip install -U discord.py[voice]`  
There is also a *requirements.txt* file included in the repository, if you know how to use it.

**6: Download the Travus Bot Base**  
There are two ways of downloading the bot base. Since the bot is only a base intended to be expanded upon via modules, it is recommended to use this repository as a template and clone your own version. If you do not wish to use GitHub or git, you can simply download the zipped version and unzip it.

**7: Set Up the Bot**  
Once you have a local (unzipped) copy of the bot base, you can start the *setup.py* file. The first thing you will be asked to is to enter your bot token we found in step 2. It will then ask you to enter a description of your bot, and a list of additional credits. This information will be displayed alongside the bot's profile image, and credits for the bot base when the *about* command is used. Separate entries for this command can be added for modules to credit module authors and display information about modules. See the [wiki entry about modules](https://github.com/Travus/Travus_Bot_Base/wiki/Module_Creation) for more information on this.

---
### Contact & Credits

**Contact**  
If you need to get in contact with me for any reason, feel free to send me a message via Discord, Twitter, or leave an issue on this repository if applicable. That said, your best bet is probably to reach me on Discord. If the fact that I made a framework for Discord bots didn't give it away, I use Discord *a lot*.  
> Discord: Travus#8888  
> Twitter: [@RealTravus](https://twitter.com/realtravus)  
> [Open a GitHub Issue](https://github.com/Travus/Travus_Bot_Base/issues/new)  
> Email: tbb@travus.dev  

**Credits**  
The *Travus Bot Base* is made by [Travus](https://github.com/Travus).  
[Discord.py](https://github.com/Rapptz/discord.py) is made by [Rapptz](https://github.com/Rapptz) and the other contributors to the project.  
[asqlite](https://gist.github.com/Rapptz/c1ff9fc7dc15194f305eb13e6cb57de1) is made by [Rapptz](https://github.com/Rapptz).

The *Travus Bot Base* is made under the [MIT License](LICENSE.md), meaning you are welcome to change, redistribute, and use it however you see fit. I am not liable for any problems you may encounter by using the bot base.
