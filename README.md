# RTBF Auvio
Kodi plugin to stream content from the RTBF Auvio website (public broadcasting organization of the French Community of Belgium)
For feature requests / issues:
https://github.com/rickybiscus/plugin.video.auvio/issues
Contributions are welcome:
https://github.com/rickybiscus/plugin.video.auvio

## Features
* Main menu : 'En direct', 'Accueil', 'Chaînes', 'Catégories', 'Mon Auvio'
* Stream live videos and radios, video replays and audio podcasts

## Installation

### Raspberry Pi (LibreELEC, OpenELEC, OSMC)
* Connect to your RPI via SSH
* Navigate to your `.kodi/addons/` folder: `cd .kodi/addons/`
* Fetch the plugin (download, extract then remove the master.zip) : `wget https://github.com/rickybiscus/plugin.video.auvio/archive/master.zip; unzip master.zip; rm master.zip`
* Rename the new folder in "plugin.video.auvio": `mv plugin.video.auvio-master plugin.video.auvio`
* (Re)start Kodi: `reboot`

### Other
* Navigate to your `.kodi/addons/` folder
* Clone this repository: `git clone https://github.com/rickybiscus/plugin.video.auvio.git`
* (Re)start Kodi.

## TODO

## License
See the `LICENSE` file.

Additional copyright notices:
* [SimplePlugin](https://github.com/romanvm/script.module.simpleplugin/stargazers) by romanvm
* [Python Slugify](https://github.com/un33k/python-slugify) by un33k
