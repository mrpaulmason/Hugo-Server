CREATE TABLE `places` (
  `place_id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `facebook_id` VARCHAR(255),
  `name` VARCHAR(255),
  `description` LONGTEXT,
  `category_id` int(11) unsigned,
  `location_data` LONGTEXT,
  `meta_data` LONGTEXT,
  `visit_count` int(11) unsigned,
  `latitude` DECIMAL,
  `longitude` DECIMAL,
  PRIMARY KEY (`place_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
