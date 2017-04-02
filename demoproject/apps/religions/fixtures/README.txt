If you want to have your fixtures to be installed during syncdb I believe you need to call the file initial_data.<ext>


Check this also:

http://docs.djangoproject.com/en/dev/howto/initial-data/#automatically-loading-initial-data-fixtures





NOTE that loading the fixtures might result in a strange error

IntegrityError: (1452, 'Cannot add or update a child row: a foreign key constraint fails (`demos_data`.`religions_religionincountry`, CONSTRAINT `country_id_refs_id_3f6cc501` FOREIGN KEY (`country_id`) REFERENCES `religions_country` (`id`))')

I should reconstruct the DB dump but for the moment it's enough to do this: 


1) remove the two constraints on the `religions_religionincountry` table from a MySQL shell


2) load the data

bash-3.2$ python manage.py loaddata religions.json
Installed 1596 object(s) from 1 fixture(s)


3) reinstall the constraints: 

ALTER TABLE `religions_religionincountry` ADD CONSTRAINT `country_id_refs_id_3f6cc501` FOREIGN KEY (`country_id`) REFERENCES `religions_country` (`id`);
ALTER TABLE `religions_religionincountry` ADD CONSTRAINT `religion_id_refs_id_10516b01` FOREIGN KEY (`religion_id`) REFERENCES `religions_religion` (`id`);