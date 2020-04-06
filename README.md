# Linky Energy Sensor

## Contexte

Le compteur Linky est un compteur électrique communiquant déployé en France par le gestionnaire de réseau Enedis.
Il dispose d'un port de TéléInformation Client (TIC), en libre accès pour l'abonné. Il s'agit d'un bus série où sont émises des statistiques de consommation : les index de consommation en cours, la puissance maximale (dite puissance de coupure), la puissance apparente instantannée consommée, la plage tarifaire ("Heures Pleines"/"Heures Creuses"), etc.
Ces informations peuvent être utiles pour une centrale de gestion d'énergie de type "Smart Home" avec production d'énergie, recharge de véhicule électrique... Elles peuvent également donner une information fiable sur ses _mauvaises_ habitudes de consommation électrique.

## Description

Ce projet est un service Linux écrit en Python, destiné à collecter les informations issues d'une TIC Linky configuré en mode **Standard**.

Les données sont aggrégées en JSON et envoyées dans une file MQTT.

:warning: Ce projet est purement software. Cette page décrit également *pour information* le matériel utilisé. Le hardware est connecté à un compteur électique : vous effectuez ceci à vos risques et périls.
:warning: Vraiment, j'insiste, dans "compteur électrique", il y a "électrique". 220 volts.

## Documentation

Spécification du protocole de communication sur le port TIC : [Sorties de télé-information client des appareils de comptage Linky utilisés en généralisation par Enedis](https://www.enedis.fr/sites/default/files/Enedis-NOI-CPT_54E.pdf)

## Hardware

J'utilise :

* un RaspberryPi 2B.
Cette board dispose de plein de GPIOs, dont certains sont mappés directement via une UART à un port série matériel.
Attention, les RPI3 demandent un peu d'adaptation (désactiver le bluetooth, et réaffecter le port série matériel à certains GPIOs). [La procédure est décrite ici](https://hallard.me/enable-serial-port-on-raspberry-pi/)
* Une board pour effectuer la liaison entre la TIC et le port série du RPI.
J'utilise la [PiTinfo de Charles Hallard](http://hallard.me/pitinfov12/), dont le design est open source (belle initiative !). Il la [vend sur Tindie](https://www.tindie.com/products/Hallard/pitinfo/).
J'utilisais précédement une RPIDom v1 de Yadom. Elle a très bien fonctionné avec une TIC en mode Historique, mais je n'ai jamais réussi à l'adapter pour la faire fonctionner en mode Standard.
Pourquoi ne pas directement connecter le port TIC aux GPIOs du RPI? C'est une mauvaise idée, car les compteurs ne garantissent pas la tension de sortie du port TIC : il faut un montage avec un optocoupleur pour garantir sa sécurité électrique. Pour avoir un signal propre et limiter les erreurs, il est conseillé d'ajouter un transistor.

## Installation

### Prérequis

Disposer de Python, d'Ansible et d'un client ssh

### Procédure

1. Installer un RPI avec une Raspbian Buster lite toute fraîche, en ayant activé le serveur ssh
1. Préconfigurer le PI, notamment en disposant d'un utilisateur avec des droits sudo et une authentification par clé SSH. Pour aller plus vite, utiliser la [playbook d'init disponible ici](TODO)
1. Ecrire un inventaire Ansible
TODO
1. Exécuter :
ansible-playbook -i <path_to_inventory>/inventory.txt deploy_linky-sensor.yml

### Configuration

TODO

## FAQ

**Je n'ai pas de compteur Linky**
Les compteurs électriques "CBE" sont également dotés d'un port TIC. Il existe déjà pléthore projets qui font cela pour ces compteurs.

**Quelle est la différence entre le mode Standard et le mode Historique?**
Le mode Historique d'une TIC Linky fonctionne exactement comme une TIC d'un compteur CBE.
Le mode Standard apporte quelques changements :

* La vitesse de transmission est plus rapide
* Les données sont horodatées (alors que les anciens compteurs CBE ne disposent pas d'horloge)
* Le compteur donne des informations supplémentaires sur le contrat : la grille tarifaire, le tarif en cours, les pointes mobiles, 10 index pour le fournisseur, 4 index pour le distributeur, les contacts secs virtuels...
* Il donne aussi supplémentaires sur la distribution d'énergie, comme la tension instantanée...

**La TIC de mon compteur est en mode Standard, comment la passer en Historique?**
Il suffit d'appeler son fournisseur d'énergie (c'est-à-dire l'entreprise qui vous facture votre électricité), et de demander "une téléopération sur votre compteur Linky pour programmer la TIC en mode Standard". Cette opération est gratuite, elle ne nécessite pas l'intervention physique d'un technicien et effectuée sous 24h en général.

Il est inutile d'appeler Enedis : le distributeur ne traite pas ces demandes émanant des clients finaux, et il est très probable que le conseiller au téléphone n'y comprenne d'ailleurs rien.

:warning: Si vous disposez d'un gestionnaire d'énergie branché sur le port TIC, vous risquez de le rendre inopérant. Renseignez-vous au préalable sur sa compatibilité, et assurez-vous que vous savez ce que vous faites!
