<p align="center">
    <img src="https://i.imgur.com/EekoTeO.png" alt="Travus Bot Base" width="450"/>
</p>
<br/>
<p align="center">
    <img alt="Python Version" src="https://img.shields.io/badge/python-3.6%20%7C%203.7%20%7C%203.8-informational"/>
    <img alt="TBB License" src="https://img.shields.io/github/license/travus/travus_bot_base">
    <a href="https://twitter.com/intent/follow?user_id=902258623690231810">
        <img alt="Twitter Follow" src="https://img.shields.io/twitter/follow/RealTravus?style=social">
    </a>
</p>
<br/><br/>

This is the Travus Bot Base, a basic starting point for Discord bots using [Discord.py](https://github.com/Rapptz/discord.py). The bot comes with all the basic functionality you need and is intended to be further extended with functionality specific to your needs. The basic included functionality is managing prefix, hiding and disabling commands, easily generating rich help entries for commands and displaying information about the bot. The main draw of the Travus Bot Base framework is its easy extendability. The bot can technically work in multiple servers at once, but this is not intended as all settings and modules will be global across all servers. To run the bot with independent settings in different servers, run multiple separate instances of it.

The intended use-case for this bot base is to be used by small to medium servers as a starting-point to build a bot for their server from. All essential functions such as changing prefix and such are already set up, and additional functionality can be added via 'modules' which can be loaded and unloaded on-the-fly without restarting the bot or disrupting other modules that might be loaded. This bot is not very feature backed, as it is intended to be a starting point to make you own custom bots from, as such it does not come with any bells and whistles outside of generic commands for maintaining bot-wide functionality such as prefixes, command help, turning commands on and off, adding and removing additional functions, and so forth. There is however a development module included which can be used to aid in development. See [included commands](https://github.com/Travus/Travus_Bot_Base/wiki/Commands) for more information on commands, including the development commands.

---

### Table of Contents

- [Installation](#installation)
- [Included Commands](https://github.com/Travus/Travus_Bot_Base/wiki/Commands)
- [Making Your Own Modules](https://github.com/Travus/Travus_Bot_Base/wiki/Module-Creation)
- [Documentation](https://github.com/Travus/Travus_Bot_Base/wiki/Documentation)
- [Additional Customization](https://github.com/Travus/Travus_Bot_Base/wiki/Customization)
- [Contact & Credits](#contact--credits)

---
### Installation
> **_NOTE:_**  
> This bot can be run standalone with it's own database via a single docker-compose command. **This will be referred to as option A.** Alternatively, if you already have a pre-existing [PostgreSQL](https://www.postgresql.org/) database, then the bot can be set up to use the existing database instead. In this case the bot can either be run directly or inside a docker container. **This will be referred to as option B.**

<br/>

**Requirements:**
* [Python](https://www.python.org/) 3.6 or newer.  
* **Option A**: [Docker](https://www.docker.com/) and [docker-compose](https://docs.docker.com/compose/)  
* **Option B**: An existing [PostgreSQL database](https://www.postgresql.org/)

**1: Create a Discord Application with Bot**  
First, you need to set up a Discord bot account, this is a special account your bot is going to use to send messages and read channels. In order to do this, you need to go to [Discord's Developer Portal](https://discord.com/developers/applications/). From here, press the *New Application* button in the top right, and give it a name. Next, on the panel to the left, navigate to the *Bot* tab. Here, click the *Add Bot* button on the right, and confirm.

**2: Set Bot Name, Image & Get the Token**  
Here you can choose the bot's name, and profile image. You can also choose whether only you, or everyone with the invite link - which we will come back to - can invite the bot. There are also two on-off toggles on this page called `Presence Intent` and `Server Member Intent`, enable both of these. Lastly, you can click the *Click to Reveal Token* text, to see your bot token. We will use this token later, so make a note of it. Also make extra sure this token does not get into the wrong hands, as everyone with the token will be able to run *any* code using your bot.

**3: Invite the Bot**  
Lastly, go back to the *General Information* page via the panel on the left. Take the 18 digit number listed as *CLIENT ID* from here, and insert it into the *Client ID* field on [this website](https://discordapi.com/permissions.html). Check the permissions you want to give your bot, and click the link it generates at the bottom of the page. Using this you can invite your bot to your server, as long as you have the manage server permission on it. You can later change these permissions by changing the role that Discord is going to create for your bot in the servers you add it to.

**4: Download and Setup**  
Now that you have set up the Discord side of the bot, you need to get the program that runs the bot ready. First download the code in this repository, either by using it as a template for a repository of your own which you then clone to your local computer, or by just downloading it directly and extracting it from the zip file GitHub gives you. Now open your terminal or command prompt and navigate into the folder you cloned or downloaded. Then, run one of the following commands depending on how you want to run the bot. (See note above requirements.)  

*Option A*:  
`pip3 install -r setup_requirements.txt`  

*Option B*:  
`pip3 install -r requirements.txt`

After you have run this command and pip is done installing the required dependencies, start the *setup.py* file that came with the *Travus Bot Base*. Give it the bot token you took a note of in step 2 when it asks for your token and give it the rest of the information it asks for.

**5: Start the Bot**  
Now that you have generated the required config file with the *setup.py* file in step 4, you can start the bot itself. This step will go over how to start and stop the bot. Once this step is reached the bot can be started simply by repeating this step, steps 1-4 do not need to be done more than once.

*Option A*:  
To start the bot simply run: `docker-compose up --build -d`  
To stop the bot simply run: `docker-compose down`  

*Option B*:  
To start the bot simply run `main.py` in Python 3.6 or newer.  
To stop the bot simply interrupt the program with `ctrl + c` or by closing the terminal.

**6: Configure the Bot (Optional)**  
Now that you have started the bot, you can change its settings from inside Discord via bot commands. The settings you can change include; [changing the bot prefix](https://github.com/Travus/Travus_Bot_Base/wiki/Commands#changing-prefix), setting whether the bot should [delete command triggers or not](https://github.com/Travus/Travus_Bot_Base/wiki/Commands#deleting-command-triggers), and writing the [bot description and additional credit sections](https://github.com/Travus/Travus_Bot_Base/wiki/Commands#customize-bot-information) for the about command. For more information see the [command reference page](https://github.com/Travus/Travus_Bot_Base/wiki/Commands).  

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

The *Travus Bot Base* is made under the [MIT License](LICENSE.md), meaning you are welcome to change, redistribute, and use it however you see fit. I am not liable for any problems you may encounter by using the bot base.
