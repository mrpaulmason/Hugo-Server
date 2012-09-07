CREATE TABLE `users` (
  `user_id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `facebook_id` VARCHAR(255),
  `facebook_auth_key` VARCHAR(255),
  `facebook_expires` int(11),
  `name` VARCHAR(129),
  `first_name` VARCHAR(64),
  `last_name` VARCHAR(64),
  `current_location` VARCHAR(64),
  `picture` VARCHAR(255),
  `friends` LONGTEXT,
  PRIMARY KEY (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
