CREATE TABLE `hugo_friends` (
  `uid1` int(11) unsigned NOT NULL,
  `uid2` int(11) unsigned NOT NULL,
  PRIMARY KEY (`uid1`, `uid2`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
