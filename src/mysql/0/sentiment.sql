CREATE TABLE `sentiment` (
  `place_id` int(11) unsigned NOT NULL,
  `user_id` int(11) unsigned NOT NULL,
  `last_timestamp` int(11) unsigned, 
  `been_here` int(11) not null default 0,
  `want_to_visit` int(1) not null default 0,
  PRIMARY KEY (`place_id`, `user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
